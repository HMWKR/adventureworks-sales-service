/* ============================================================
   예측 플레이그라운드 — /api/predict/* 호출 + Toss 결과 렌더
   ============================================================ */
(function () {
  const CH = window.__CHOICES__ || {};
  const $ = (id) => document.getElementById(id);
  const money = (v) => v == null ? '-' :
    (Math.abs(v) >= 1e6 ? '$' + (v / 1e6).toFixed(2) + 'M'
      : '$' + Number(v).toLocaleString(undefined, { maximumFractionDigits: 2 }));
  const GLO = window.__GLOSSARY__ || {};
  // value 는 영어(모델 입력값) 유지, 표시 텍스트만 "English · 한국어"
  const fill = (sel, arr, pref, kind) => {
    const g = (kind && GLO[kind]) || {};
    sel.innerHTML = arr.map(v => {
      const ko = g[v] ? ' · ' + g[v].ko : '';
      return `<option value="${v}" ${v === pref ? 'selected' : ''}>${v}${ko}</option>`;
    }).join('');
  };
  const spin = (el) => { el.className = 'result'; el.innerHTML = '<div class="spin"></div>'; };
  const errCard = (el, msg) => {
    el.className = 'result err';
    el.innerHTML = `<div class="r-label">⚠️ 오류</div><div class="r-big">${msg}</div>`;
  };

  /* 드롭다운 채우기 */
  fill($('s-cat'), CH.categories || [], 'Bikes', 'category');
  fill($('s-sub'), CH.subcategories || [], 'Road Bikes');
  fill($('s-ch'), CH.channels || [], 'Reseller', 'channel');
  fill($('s-region'), CH.regions || [], 'Southwest', 'region');
  // 구매 예측 드롭다운
  fill($('b-region'), CH.regions || [], 'Southwest', 'region');
  fill($('b-ch'), CH.channels || [], 'Reseller', 'channel');
  fill($('b-cat'), CH.categories || [], 'Bikes', 'category');

  /* 세그먼트 컨트롤 */
  document.querySelectorAll('.seg button').forEach(b => b.addEventListener('click', () => {
    document.querySelectorAll('.seg button').forEach(x => x.classList.remove('active'));
    document.querySelectorAll('.tool').forEach(x => x.classList.remove('active'));
    b.classList.add('active');
    $('tool-' + b.dataset.tool).classList.add('active');
  }));

  async function postJSON(url, body) {
    const r = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body) });
    const data = await r.json();
    if (!r.ok) throw new Error(data.detail || ('HTTP ' + r.status));
    setTimeout(loadRecent, 200);   // 예측 직후 기록 갱신(서버 로그 반영)
    return data;
  }

  /* 최근 예측 기록 (Supabase/로컬) */
  const KIND_KO = { buy: '구매예측', sales: '매출예측', segment: '세그먼트' };
  function summarize(it) {
    const i = it.inputs || {}, o = it.output || {};
    if (it.kind === 'buy') return `${i.region}·${i.category} → ${o.label} (${((o.buy_probability||0)*100).toFixed(0)}%)`;
    if (it.kind === 'sales') return `${i.category}·${i.region} → $${Number(o.predicted_sales_amount||0).toLocaleString()}`;
    if (it.kind === 'segment') return `R${i.recency}·F${i.frequency}·M${i.monetary} → ${o.segment}`;
    return JSON.stringify(o);
  }
  async function loadRecent() {
    try {
      const r = await fetch('/api/predictions/recent?limit=8');
      const d = await r.json();
      const badge = $('log-source');
      if (badge) { badge.textContent = d.source === 'supabase' ? 'Supabase 저장' : '로컬 저장';
        badge.className = 'log-badge ' + (d.source === 'supabase' ? 'supabase' : 'local'); }
      const box = $('recent-list');
      if (!box) return;
      if (!d.items || !d.items.length) {
        box.innerHTML = '<div class="placeholder" style="padding:14px">아직 기록이 없어요. 위에서 예측을 한 번 해보세요.</div>';
        return;
      }
      // 저장형 XSS 방지: innerHTML 문자열 조립 대신 DOM 생성 + textContent
      const KNOWN = { buy: 1, sales: 1, segment: 1 };
      box.replaceChildren(...d.items.map(it => {
        const row = document.createElement('div'); row.className = 'recent-row';
        const kind = document.createElement('span');
        kind.className = 'kind ' + (KNOWN[it.kind] ? it.kind : '');   // 알려진 kind만 클래스
        kind.textContent = KIND_KO[it.kind] || String(it.kind || '');
        const desc = document.createElement('span'); desc.className = 'desc';
        desc.textContent = summarize(it);
        const time = document.createElement('span'); time.className = 'time';
        time.textContent = (it.created_at || '').replace('T', ' ').slice(0, 16);
        row.append(kind, desc, time);
        return row;
      }));
    } catch (e) { /* 조용히 무시 */ }
  }
  loadRecent();

  /* 1) 매출 예측 */
  $('s-go').addEventListener('click', async () => {
    const out = $('s-result'); spin(out);
    try {
      const d = await postJSON('/api/predict/sales', {
        order_quantity: +$('s-qty').value, list_price: +$('s-list').value,
        standard_cost: +$('s-cost').value, category: $('s-cat').value,
        subcategory: $('s-sub').value, channel: $('s-ch').value, region: $('s-region').value,
      });
      out.className = 'result';
      out.innerHTML = `<div class="r-label">💰 예측 매출액</div>
        <div class="r-big">${money(d.predicted_sales_amount)}</div>
        <div class="r-sub">입력 조건 기준 예상 매출이에요.</div>`;
    } catch (e) { errCard(out, e.message); }
  });

  /* 2) 구매 예측 (Buy or Not Buy) */
  $('b-go').addEventListener('click', async () => {
    const out = $('b-result'); spin(out);
    try {
      const d = await postJSON('/api/predict/buy', {
        region: $('b-region').value, channel: $('b-ch').value, category: $('b-cat').value,
        prior_orders: +$('b-orders').value, prior_monetary: +$('b-mon').value,
      });
      const pct = (d.buy_probability * 100).toFixed(1);
      const color = d.will_buy ? '#1bbf83' : '#f04452';
      out.className = 'result';
      out.innerHTML = `<div class="r-label">🛒 구매 예측 결과</div>
        <div><span class="r-badge" style="background:${color}">${d.label}</span></div>
        <div class="r-sub">구매 확률 <b>${pct}%</b></div>
        <div class="prob"><div class="prob-row">
          <span class="name">구매 확률</span>
          <span class="bar"><i style="width:${pct}%;background:${color}"></i></span>
          <span class="pct">${pct}%</span></div></div>`;
    } catch (e) { errCard(out, e.message); }
  });

  /* 3) 세그먼트 예측 */
  $('g-go').addEventListener('click', async () => {
    const out = $('g-result'); spin(out);
    try {
      const d = await postJSON('/api/predict/segment', {
        recency: +$('g-r').value, frequency: +$('g-f').value, monetary: +$('g-m').value,
      });
      const probs = Object.entries(d.probabilities).slice(0, 5);
      const bars = probs.map(([k, v]) => `<div class="prob-row">
        <span class="name">${k}</span><span class="bar"><i style="width:${(v * 100).toFixed(1)}%"></i></span>
        <span class="pct">${(v * 100).toFixed(1)}%</span></div>`).join('');
      out.className = 'result';
      out.innerHTML = `<div class="r-label">🎯 예측 세그먼트</div>
        <div><span class="r-badge">${d.segment}</span></div>
        <div class="r-sub">확신도 ${(d.confidence * 100).toFixed(1)}%</div>
        <div class="prob">${bars}</div>`;
    } catch (e) { errCard(out, e.message); }
  });

  /* 3) 시계열 예측 */
  const fh = $('f-h');
  fh.addEventListener('input', () => $('f-h-label').textContent = fh.value);
  let fcChart = null;
  $('f-go').addEventListener('click', async () => {
    try {
      const r = await fetch('/api/predict/forecast?horizon=' + fh.value);
      const d = await r.json();
      const hist = d.history || [], fc = d.forecast || [];
      const x = hist.map(p => p.month).concat(fc.map(p => p.month));
      const actual = hist.map(p => p.sales_amount).concat(fc.map(() => null));
      const forecast = hist.map(() => null);
      if (hist.length) forecast[hist.length - 1] = hist[hist.length - 1].sales_amount;
      fc.forEach(p => forecast.push(p.forecast_sales_amount));
      const INK3 = '#8b95a1', LINE = '#f2f4f6', BLUE = '#3182f6';
      if (!fcChart) fcChart = echarts.init($('chart-forecast'));
      fcChart.setOption({
        grid: { left: 8, right: 18, top: 30, bottom: 8, containLabel: true },
        legend: { top: 0, right: 0, data: ['실제', '예측'], textStyle: { color: '#4e5968', fontSize: 11 } },
        tooltip: {
          trigger: 'axis', backgroundColor: '#191f28', borderWidth: 0, textStyle: { color: '#fff' },
          formatter: p => { const v = p.find(o => o.data != null); return v ? `${v.axisValue}<br/><b>${money(v.data)}</b> (${v.seriesName})` : ''; },
        },
        xAxis: { type: 'category', data: x, boundaryGap: false,
          axisLine: { lineStyle: { color: LINE } }, axisTick: { show: false },
          axisLabel: { color: INK3, fontSize: 10, interval: 5 } },
        yAxis: { type: 'value', axisLine: { show: false }, axisTick: { show: false },
          splitLine: { lineStyle: { color: LINE } },
          axisLabel: { color: INK3, fontSize: 10, formatter: v => money(v) } },
        series: [
          { name: '실제', type: 'line', data: actual, smooth: true, symbol: 'none',
            lineStyle: { color: BLUE, width: 3 },
            areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1,
              [{ offset: 0, color: 'rgba(49,130,246,.22)' }, { offset: 1, color: 'rgba(49,130,246,.02)' }]) } },
          { name: '예측', type: 'line', data: forecast, smooth: true, symbol: 'circle', symbolSize: 6,
            lineStyle: { color: '#f04452', width: 3, type: 'dashed' }, itemStyle: { color: '#f04452' } },
        ],
      });
    } catch (e) { console.error(e); }
  });

  window.addEventListener('resize', () => fcChart && fcChart.resize());
  // 시계열 탭 첫 진입 시 자동 1회 실행
  document.querySelector('.seg button[data-tool="forecast"]').addEventListener('click', () => {
    if (fcChart) return; setTimeout(() => $('f-go').click(), 60);
  });
})();
