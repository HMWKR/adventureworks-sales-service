/* ============================================================
   AdventureWorks 스토리 대시보드 — ECharts 렌더링
   window.__DATA__ (서버 주입)로부터 차트를 그린다.
   ============================================================ */
(function () {
  const D = window.__DATA__ || {};
  const C = (D.charts) || {};

  // 디자인 토큰(차트용)
  const BLUE = '#3182f6', BLUE2 = '#69a7ff', INK2 = '#4e5968', INK3 = '#8b95a1', LINE = '#f2f4f6';
  const PALETTE = ['#3182f6', '#69a7ff', '#9ec5ff', '#1bbf83', '#ff9500', '#f04452', '#845ef7'];

  // 통화 포맷
  const money = (v) => {
    if (v == null) return '-';
    if (Math.abs(v) >= 1e6) return '$' + (v / 1e6).toFixed(1) + 'M';
    if (Math.abs(v) >= 1e3) return '$' + (v / 1e3).toFixed(0) + 'K';
    return '$' + Math.round(v).toLocaleString();
  };
  const axisStyle = { axisLine: { lineStyle: { color: LINE } }, axisTick: { show: false },
                      axisLabel: { color: INK3, fontSize: 11 } };
  const grid = { left: 8, right: 18, top: 24, bottom: 8, containLabel: true };
  const charts = [];
  function mk(id, opt) {
    const el = document.getElementById(id);
    if (!el) return;
    const c = echarts.init(el);
    c.setOption(opt);
    charts.push(c);
  }
  const tip = (fmt) => ({ trigger: 'axis', backgroundColor: '#191f28', borderWidth: 0,
    textStyle: { color: '#fff', fontSize: 12 }, padding: [8, 12], formatter: fmt });

  /* 1) 월별 매출 추이 — 그라데이션 영역 라인 */
  (function () {
    const m = C.monthly || [];
    const x = m.map(d => d.YearMonth), y = m.map(d => d.sales_amount);
    mk('chart-monthly', {
      grid, tooltip: tip(p => `${p[0].axisValue}<br/><b>${money(p[0].data)}</b>`),
      xAxis: { type: 'category', data: x, boundaryGap: false, ...axisStyle,
               axisLabel: { color: INK3, fontSize: 10, interval: 5 } },
      yAxis: { type: 'value', ...axisStyle, splitLine: { lineStyle: { color: LINE } },
               axisLabel: { color: INK3, fontSize: 10, formatter: v => money(v) } },
      series: [{
        type: 'line', data: y, smooth: true, symbol: 'none',
        lineStyle: { color: BLUE, width: 3 },
        areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1,
          [{ offset: 0, color: 'rgba(49,130,246,.28)' }, { offset: 1, color: 'rgba(49,130,246,.02)' }]) },
        markPoint: { symbolSize: 46, data: [{ type: 'max', name: '최고' }],
          itemStyle: { color: BLUE }, label: { color: '#fff', fontSize: 10, formatter: o => money(o.value) } },
      }],
    });
  })();

  /* 2) 카테고리 구성 — 도넛 */
  (function () {
    const c = C.category || [];
    mk('chart-category', {
      tooltip: { trigger: 'item', backgroundColor: '#191f28', borderWidth: 0,
        textStyle: { color: '#fff' }, formatter: p => `${p.name}<br/><b>${money(p.value)}</b> (${p.percent}%)` },
      legend: { bottom: 0, textStyle: { color: INK2, fontSize: 11 }, icon: 'circle' },
      color: PALETTE,
      series: [{
        type: 'pie', radius: ['46%', '72%'], center: ['50%', '44%'], avoidLabelOverlap: true,
        itemStyle: { borderColor: '#fff', borderWidth: 3, borderRadius: 6 },
        label: { formatter: '{b}\n{d}%', color: INK2, fontSize: 11, fontWeight: 600 },
        data: c.map(d => ({ name: d.Category, value: d.sales_amount })),
      }],
    });
  })();

  /* 3) 지역별 매출 TOP — 수평 막대 */
  (function () {
    const r = (C.region || []).slice(0, 10).reverse();
    mk('chart-region', {
      grid: { ...grid, left: 8 }, tooltip: tip(p => `${p[0].axisValue}<br/><b>${money(p[0].data)}</b>`),
      xAxis: { type: 'value', ...axisStyle, splitLine: { lineStyle: { color: LINE } },
               axisLabel: { color: INK3, fontSize: 10, formatter: v => money(v) } },
      yAxis: { type: 'category', data: r.map(d => d.Region), ...axisStyle,
               axisLabel: { color: INK2, fontSize: 11 } },
      series: [{ type: 'bar', data: r.map(d => d.sales_amount), barWidth: '58%',
        itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 1, 0,
          [{ offset: 0, color: BLUE2 }, { offset: 1, color: BLUE }]), borderRadius: [0, 6, 6, 0] } }],
    });
  })();

  /* 4) 베스트셀러 제품 — 수평 막대 */
  (function () {
    const p = (C.top_products || []).slice(0, 10).reverse();
    mk('chart-products', {
      grid: { ...grid, left: 8 }, tooltip: tip(t => `${t[0].axisValue}<br/><b>${money(t[0].data)}</b>`),
      xAxis: { type: 'value', ...axisStyle, splitLine: { lineStyle: { color: LINE } },
               axisLabel: { color: INK3, fontSize: 10, formatter: v => money(v) } },
      yAxis: { type: 'category', data: p.map(d => d.Product), ...axisStyle,
               axisLabel: { color: INK2, fontSize: 10, width: 130, overflow: 'truncate' } },
      series: [{ type: 'bar', data: p.map(d => d.sales_amount), barWidth: '58%',
        itemStyle: { color: '#1bbf83', borderRadius: [0, 6, 6, 0] } }],
    });
  })();

  /* 5) 세그먼트별 고객 수 */
  (function () {
    const s = C.segments || [];
    mk('chart-seg-cnt', {
      grid, tooltip: tip(p => `${p[0].axisValue}<br/><b>${p[0].data.toLocaleString()}명</b>`),
      xAxis: { type: 'category', data: s.map(d => d.Segment), ...axisStyle,
               axisLabel: { color: INK2, fontSize: 10, interval: 0, rotate: 18 } },
      yAxis: { type: 'value', ...axisStyle, splitLine: { lineStyle: { color: LINE } },
               axisLabel: { color: INK3, fontSize: 10 } },
      series: [{ type: 'bar', data: s.map(d => d.customers), barWidth: '52%',
        itemStyle: { color: BLUE, borderRadius: [6, 6, 0, 0] } }],
    });
  })();

  /* 6) 세그먼트별 매출 기여 */
  (function () {
    const s = C.segments || [];
    mk('chart-seg-rev', {
      grid, tooltip: tip(p => `${p[0].axisValue}<br/><b>${money(p[0].data)}</b>`),
      xAxis: { type: 'category', data: s.map(d => d.Segment), ...axisStyle,
               axisLabel: { color: INK2, fontSize: 10, interval: 0, rotate: 18 } },
      yAxis: { type: 'value', ...axisStyle, splitLine: { lineStyle: { color: LINE } },
               axisLabel: { color: INK3, fontSize: 10, formatter: v => money(v) } },
      series: [{ type: 'bar', data: s.map(d => d.total_monetary), barWidth: '52%',
        itemStyle: { color: '#845ef7', borderRadius: [6, 6, 0, 0] } }],
    });
  })();

  /* 7) 실제 vs 예측 월매출 — 실선 + 점선 투영 */
  (function () {
    const f = C.forecast || { history: [], forecast: [] };
    const hist = f.history || [], fc = f.forecast || [];
    const x = hist.map(d => d.month).concat(fc.map(d => d.month));
    const actual = hist.map(d => d.sales_amount).concat(fc.map(() => null));
    // 예측선을 실제선 마지막 점에서 이어지게
    const fcVals = fc.map(d => d.forecast_sales_amount);
    const lastActual = hist.length ? hist[hist.length - 1].sales_amount : null;
    const forecast = hist.map(() => null);
    if (hist.length) forecast[hist.length - 1] = lastActual;
    fcVals.forEach(v => forecast.push(v));
    mk('chart-forecast', {
      grid, legend: { top: 0, right: 0, textStyle: { color: INK2, fontSize: 11 },
        data: ['실제', '예측'], icon: 'roundRect' },
      tooltip: tip(p => {
        const v = p.find(o => o.data != null);
        return v ? `${v.axisValue}<br/><b>${money(v.data)}</b> (${v.seriesName})` : '';
      }),
      xAxis: { type: 'category', data: x, boundaryGap: false, ...axisStyle,
               axisLabel: { color: INK3, fontSize: 10, interval: 5 } },
      yAxis: { type: 'value', ...axisStyle, splitLine: { lineStyle: { color: LINE } },
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
  })();

  /* 반응형 */
  window.addEventListener('resize', () => charts.forEach(c => c.resize()));

  /* 스크롤 등장 애니메이션 */
  const io = new IntersectionObserver((entries) => {
    entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('show'); io.unobserve(e.target); } });
  }, { threshold: 0.12 });
  document.querySelectorAll('.reveal').forEach(el => io.observe(el));
})();
