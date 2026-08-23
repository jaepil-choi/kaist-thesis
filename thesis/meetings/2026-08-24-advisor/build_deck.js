const pptxgen = require("pptxgenjs");
const path = require("path");

// 저장소 루트는 이 스크립트 위치에서 유도한다. THESIS_REPO로 덮어쓸 수 있다.
const REPO = process.env.THESIS_REPO || path.resolve(__dirname, "..", "..", "..");
const FIG = path.join(REPO, "guijarro-ordonez-2025-replication", "paper-assets", "figures");
const OUT = process.env.DECK_OUT || path.join(__dirname, "advisor-meeting-guijarro-korea.pptx");

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5
pres.author = "Jaepil Choi";
pres.title = "딥러닝 통계적 차익거래의 한국시장 재현";

// ---- simple monochrome palette ----
const INK = "111111";
const GRAY = "555555";
const LGRAY = "8C8C8C";
const RULE = "D9D9D9";
const BAND = "F4F4F4";
const F = "Malgun Gothic";

const M = 0.65;
const CW = 13.33 - 2 * M; // 12.03

let pageNo = 0;

function slide(title, kicker) {
  pageNo += 1;
  const s = pres.addSlide();
  s.background = { color: "FFFFFF" };
  if (kicker) {
    s.addText(kicker, {
      x: M, y: 0.42, w: CW, h: 0.26,
      fontSize: 12, bold: true, color: LGRAY, fontFace: F, margin: 0,
    });
  }
  s.addText(title, {
    x: M, y: kicker ? 0.72 : 0.55, w: CW, h: 0.62,
    fontSize: 27, bold: true, color: INK, fontFace: F, margin: 0,
  });
  s.addText(String(pageNo), {
    x: 12.4, y: 7.0, w: 0.5, h: 0.25,
    fontSize: 10, color: LGRAY, fontFace: F, align: "right", margin: 0,
  });
  return s;
}

function note(s, txt, y) {
  s.addText(txt, {
    x: M, y: y, w: CW, h: 0.3,
    fontSize: 10.5, color: LGRAY, fontFace: F, italic: true, margin: 0,
  });
}

function tableOpts(colW) {
  return {
    x: M, w: CW, colW: colW,
    border: [
      { type: "none" },
      { type: "none" },
      { type: "solid", color: RULE, pt: 0.75 },
      { type: "none" },
    ],
    fontFace: F, fontSize: 12, color: INK,
    valign: "middle", autoPage: false,
  };
}

function hdr(t) {
  return { text: t, options: { bold: true, color: INK, fill: { color: BAND } } };
}

// =====================================================================
// S1  Title
// =====================================================================
{
  pageNo += 1;
  const s = pres.addSlide();
  s.background = { color: "FFFFFF" };
  s.addText("KAIST MFE 학위논문 · 지도교수 미팅", {
    x: M, y: 1.75, w: CW, h: 0.3, fontSize: 13, color: LGRAY, fontFace: F, margin: 0,
  });
  s.addText("딥러닝 통계적 차익거래의 한국시장 재현", {
    x: M, y: 2.15, w: CW, h: 0.75, fontSize: 36, bold: true, color: INK, fontFace: F, margin: 0,
  });
  s.addText(
    "Guijarro-Ordonez, Pelger, and Zanotti (2025), “Deep Learning Statistical Arbitrage”, Management Science",
    { x: M, y: 2.98, w: CW, h: 0.35, fontSize: 14, color: GRAY, fontFace: F, margin: 0 }
  );
  s.addShape(pres.ShapeType.line, {
    x: M, y: 3.62, w: 3.2, h: 0, line: { color: INK, width: 1 },
  });
  s.addText(
    [
      { text: "1.  논문 요약 — 통계적 차익거래의 3단계 분해", options: { breakLine: true } },
      { text: "2.  재현 결과 — 미국 원 논문과 한국 데이터 비교", options: { breakLine: true } },
      { text: "3.  논의사항 3건 — 표본기간 · 수익률 정의 · IPCA 특성변수" },
    ],
    { x: M, y: 3.95, w: CW, h: 1.1, fontSize: 14, color: INK, fontFace: F, lineSpacing: 24, margin: 0 }
  );
  s.addText("최재필  |  2026. 08. 24.", {
    x: M, y: 6.55, w: CW, h: 0.3, fontSize: 12, color: GRAY, fontFace: F, margin: 0,
  });
  s.addNotes("30분 미팅. 파트1은 3분, 파트2는 12분, 파트3 질문에 15분 배분.");
}

// =====================================================================
// S2  논문 개요
// =====================================================================
{
  const s = slide("통계적 차익거래를 세 부품으로 분해한다", "1. 논문 요약");

  const rows = [
    ["①", "차익거래 포트폴리오",
      "팩터모형 잔차를 거래 가능한 포트폴리오로 만든다.   ε = Φ R,   Φ = I − β W_Fᵀ\n개별종목 롱 + 동일 위험노출 모방포트폴리오 숏 = 시장중립 상대가치 거래"],
    ["②", "차익거래 신호",
      "최근 L = 30일 누적잔차 경로에서 시계열 패턴을 추출한다.\nCNN이 국소 패턴(추세·반전), Transformer가 전역 의존관계를 학습"],
    ["③", "차익거래 정책",
      "신호를 종목 비중으로 변환한다.  수익률 예측이 아니라 Sharpe ratio를 직접 최적화하고,\n비중 절댓값 합을 1로 고정해 레버리지를 제약"],
  ];

  let y = 1.62;
  rows.forEach(([num, head, body]) => {
    s.addText(num, {
      x: M, y: y, w: 0.5, h: 0.45, fontSize: 22, bold: true, color: LGRAY, fontFace: F, margin: 0,
    });
    s.addText(head, {
      x: M + 0.55, y: y, w: 3.1, h: 0.4, fontSize: 16, bold: true, color: INK, fontFace: F, margin: 0,
    });
    s.addText(body, {
      x: M + 3.7, y: y - 0.02, w: CW - 3.7, h: 0.95, fontSize: 12.5, color: GRAY,
      fontFace: F, lineSpacing: 19, margin: 0,
    });
    y += 1.35;
  });

  s.addShape(pres.ShapeType.rect, {
    x: M, y: 5.85, w: CW, h: 0.82, fill: { color: BAND }, line: { color: BAND },
  });
  s.addText(
    [
      { text: "논문의 핵심 주장 : ", options: { bold: false, color: GRAY } },
      { text: "세 부품 중 ②신호 추출이 성과를 가르는 결정적 요소다.", options: { bold: true, color: INK } },
    ],
    { x: M + 0.35, y: 5.85, w: CW - 0.7, h: 0.42, fontSize: 14, fontFace: F, valign: "middle", margin: 0 }
  );
  s.addText("배분 함수만 유연하게 만들어도 개선이 없고, 잔차 대신 원 수익률로 학습하면 성과가 급락한다.", {
    x: M + 0.35, y: 6.25, w: CW - 0.7, h: 0.35, fontSize: 11.5, color: GRAY, fontFace: F, margin: 0,
  });
  s.addNotes("3단계 분해가 논문의 프레임워크. 기여는 새 모형이 아니라 어느 부품이 중요한지를 분리해 보여준 것.");
}

// =====================================================================
// S3  원 논문 결과 (미국)
// =====================================================================
{
  const s = slide("원 논문 결과 — 미국, PCA5 잔차, OOS 2002–2016 (15년)", "1. 논문 요약");

  const data = [
    [hdr("정책 모형"), hdr("신호"), hdr("배분"), hdr("Sharpe ratio")],
    ["원 수익률 (K = 0)", "—", "—", "1.64"],
    ["OU + Threshold", "고정 (OU 모수)", "임계값 규칙", "0.73"],
    ["Fourier + FFN", "고정 (푸리에 기저)", "신경망", "1.95"],
    [
      { text: "CNN + Transformer", options: { bold: true } },
      { text: "데이터가 학습", options: { bold: true } },
      { text: "신경망", options: { bold: true } },
      { text: "4.16", options: { bold: true } },
    ],
  ];
  s.addTable(data, { ...tableOpts([4.3, 3.0, 2.3, 2.43]), y: 1.62, rowH: 0.42 });

  s.addText("원 논문의 세 가지 결론", {
    x: M, y: 4.25, w: CW, h: 0.32, fontSize: 15, bold: true, color: INK, fontFace: F, margin: 0,
  });
  s.addText(
    [
      { text: "잔차로 거래해야 한다.  원 수익률(K = 0)은 서로 강하게 상관되어 학습할 정보가 사실상 몇 개뿐이다.", options: { bullet: true, breakLine: true } },
      { text: "신호가 결정적이다.  Fourier + FFN과 CNN + Transformer는 배분 함수가 동일하고 신호만 다른데 1.95 → 4.16.", options: { bullet: true, breakLine: true } },
      { text: "강건하다.  Fama-French 8팩터에 대한 알파 t = 11 ~ 14, R² ≈ 0, 거래비용 반영 후에도 Sharpe 0.94 ~ 1.24 유지.", options: { bullet: true } },
    ],
    { x: M, y: 4.65, w: CW, h: 1.5, fontSize: 13, color: INK, fontFace: F, paraSpaceAfter: 10, margin: 0 }
  );
  note(s, "출처 : 원 논문 Table 1, Table 2, Table 9.  팩터 5개를 넘어서면 성과 개선이 평탄해진다.", 6.45);
  s.addNotes("Fourier+FFN 대 CNN+Trans 비교가 핵심 증거. 배분은 같고 신호만 다르다.");
}

// =====================================================================
// S4  재현 설계 대조표
// =====================================================================
{
  const s = slide("재현 설계 — 원 논문과 무엇을 같게 하고 무엇이 달라졌나", "2. 재현 결과");

  const Q = { text: "논의", options: { bold: true, color: INK, align: "center" } };
  const OKm = { text: "동일", options: { color: GRAY, align: "center" } };
  const DIF = { text: "상이", options: { color: GRAY, align: "center" } };

  const data = [
    [hdr("항목"), hdr("원 논문 (미국)"), hdr("본 연구 (한국)"), { text: "구분", options: { bold: true, color: INK, fill: { color: BAND }, align: "center" } }],
    ["원자료 기간", "1978–2016 CRSP", "2015–2026 국내 일별", DIF],
    ["잔차 표본", "1998–2016 (19년)", "2020-01-02 ~ 2026-07-20 (1,606일)", Q],
    ["정책 OOS 평가", "2002–2016 (15년)", "2024-01-19 ~ 2026-07-20 (606일, 2.4년)", Q],
    ["일별 종목수", "약 550 (S&P500 규모)", "127 ~ 185", DIF],
    ["universe 규칙", "전월말 시총 > 전체의 0.01%", "동일 규칙, KOSPI·KOSDAQ 보통주", OKm],
    ["수익률 정의", "total return (배당 포함)", "권리·분할 조정 price return, 현금배당 제외", Q],
    ["팩터 모형", "FF 1/3/5/8, PCA, IPCA", "한국 FF 1/3/5, PCA K = 0~15, IPCA 진행 예정", DIF],
    ["학습 계약", "seed 0, 1,000일 학습, 125일 재학습, 100 epoch", "동일", OKm],
    ["거래비용", "5 bp 거래 + 1 bp 공매도 보유", "동일 파라미터 적용", OKm],
  ];
  s.addTable(data, { ...tableOpts([2.35, 3.7, 4.9, 1.08]), y: 1.6, rowH: 0.375, fontSize: 11.5 });

  note(s, "‘논의’ 표시 세 항목이 오늘 여쭙고 싶은 내용입니다. (슬라이드 9 · 10 · 11)", 5.95);
  s.addNotes("이 표가 파트3 질문으로 그대로 연결된다. 논의 3개를 여기서 미리 예고.");
}

// =====================================================================
// S5  Table 1 — 미국 vs 한국 성과
// =====================================================================
{
  const s = slide("Table 1 재현 — 정책 모형별 Sharpe ratio, 미국 대 한국", "2. 재현 결과");

  const labels = ["원 수익률\n(K = 0)", "OU +\nThreshold", "Fourier +\nFFN", "CNN +\nTransformer", "CNN + Trans\n(거래비용 반영)"];
  s.addChart(
    pres.ChartType.bar,
    [
      { name: "미국 (원 논문)", labels: labels, values: [1.64, 0.73, 1.95, 4.16, 1.24] },
      { name: "한국 (본 연구)", labels: labels, values: [-0.08, 1.47, 3.27, 4.15, 1.37] },
    ],
    {
      x: M, y: 1.55, w: 7.75, h: 4.5,
      barDir: "col", barGapWidthPct: 55,
      chartColors: ["BFBFBF", "222222"],
      showTitle: false,
      showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 10,
      dataLabelColor: INK, dataLabelFontFace: F, dataLabelFormatCode: "0.00",
      showLegend: true, legendPos: "t", legendFontSize: 11, legendColor: INK,
      catAxisLabelColor: INK, catAxisLabelFontSize: 10, catAxisLabelFontFace: F,
      valAxisLabelColor: LGRAY, valAxisLabelFontSize: 10, valAxisLabelFontFace: F,
      valAxisMinVal: -1, valAxisMaxVal: 5,
      valGridLine: { color: "EDEDED", size: 1 },
      catGridLine: { style: "none" },
    }
  );

  s.addText("읽는 법", {
    x: 8.7, y: 1.62, w: 3.95, h: 0.3, fontSize: 14, bold: true, color: INK, fontFace: F, margin: 0,
  });
  s.addText(
    [
      { text: "모형 간 순서가 그대로 재현되었다.", options: { bold: true, breakLine: true } },
      { text: "OU < Fourier+FFN < CNN+Transformer.  한국에서도 신호가 유연할수록 성과가 높다.\n", options: { color: GRAY, breakLine: true } },
      { text: "CNN+Transformer는 4.15로 원 논문 4.16과 사실상 동일하다.", options: { bold: true, breakLine: true } },
      { text: "연수익률 16.8%, 연변동성 4.0%.\n", options: { color: GRAY, breakLine: true } },
      { text: "K = 0이 한국에서는 음수다.", options: { bold: true, breakLine: true } },
      { text: "미국은 1.64였다.  요인 제거의 효과가 한국에서 더 크게 나타났다.", options: { color: GRAY } },
    ],
    { x: 8.7, y: 1.95, w: 3.95, h: 3.6, fontSize: 12, color: INK, fontFace: F, lineSpacing: 17, margin: 0 }
  );

  note(s, "미국은 PCA5 기준(비용 반영은 IPCA 기준), 한국은 PCA5 기준.  한국 OOS 606일, 연율화는 원 논문 규약(252일)을 따름.", 6.35);
  s.addNotes("수치가 비슷하다고 해서 같은 경제적 성과가 아니라는 점은 파트3에서 다룬다.");
}

// =====================================================================
// S6  Table 2 — 알파 유의성
// =====================================================================
{
  const s = slide("Table 2 재현 — 알파는 기존 위험요인으로 설명되지 않는다", "2. 재현 결과");

  const data = [
    [hdr("PCA 팩터 수 K"), hdr("연 α"), hdr("t(α)"), hdr("R²"), hdr("연 μ"), hdr("t(μ)")],
    ["0  (원 수익률)", "−5.3%", "−0.81", "5.2%", "−0.8%", "−0.13"],
    ["1", "10.1%", "2.87", "0.7%", "10.6%", "3.07"],
    ["3", "17.4%", "6.20", "1.9%", "16.8%", "6.05"],
    [
      { text: "5", options: { bold: true } },
      { text: "16.7%", options: { bold: true } },
      { text: "6.31", options: { bold: true } },
      { text: "0.9%", options: { bold: true } },
      { text: "16.8%", options: { bold: true } },
      { text: "6.43", options: { bold: true } },
    ],
    ["8", "13.3%", "5.55", "1.5%", "13.0%", "5.49"],
    ["10", "12.3%", "5.53", "1.8%", "11.7%", "5.29"],
    ["15", "9.4%", "4.91", "2.7%", "8.4%", "4.39"],
  ];
  s.addTable(data, { ...tableOpts([2.6, 1.9, 1.9, 1.9, 1.9, 1.83]), y: 1.6, rowH: 0.38, align: "center" });

  s.addText(
    [
      { text: "K ≥ 1의 모든 사양에서 t(α) > 2.8 이고 R²는 3% 미만이다.", options: { bullet: true, breakLine: true } },
      { text: "알파가 평균수익과 거의 같다 (16.7% 대 16.8%).  즉 수익의 대부분이 위험 프리미엄이 아니다.", options: { bullet: true, breakLine: true } },
      { text: "K = 0에서만 유의하지 않다.  요인을 제거해야 차익거래가 성립한다는 원 논문 결론과 일치한다.", options: { bullet: true } },
    ],
    { x: M, y: 4.95, w: CW, h: 1.2, fontSize: 13, color: INK, fontFace: F, paraSpaceAfter: 9, margin: 0 }
  );
  note(s, "CNN + Transformer, Sharpe 목적함수.  알파 기준은 한국 FF5 + MOM 6팩터이며 원 논문의 FF8과는 다르다 (STREV·LTREV 정의 미확보).", 6.45);
  s.addNotes("R²가 낮다는 것이 시장중립성의 실증적 확인. 6팩터 기준이라는 단서는 반드시 언급.");
}

// =====================================================================
// S7  Figure 5
// =====================================================================
{
  const s = slide("Figure 5 재현 — 한국 표본외 누적수익률 (2024-01 ~ 2026-07)", "2. 재현 결과");

  s.addImage({ path: path.join(FIG, "fig_05_korean_cumulative_returns.png"), x: M, y: 1.6, w: CW, h: 3.85 });

  s.addText(
    [
      { text: "세 정책 모두 대부분의 잔차 사양에서 우상향하지만, 기울기와 변동폭이 뚜렷하게 다르다.", options: { bullet: true, breakLine: true } },
      { text: "빨간 선이 원 수익률(K = 0)이다.  CNN + Transformer와 Fourier + FFN 모두에서 크게 손실이 났다.", options: { bullet: true, breakLine: true } },
      { text: "누적곡선의 우상향만으로 거래가능성을 결론낼 수 없다.  다음 장의 비용 결과와 함께 보아야 한다.", options: { bullet: true } },
    ],
    { x: M, y: 5.6, w: CW, h: 1.15, fontSize: 12.5, color: INK, fontFace: F, paraSpaceAfter: 8, margin: 0 }
  );
  s.addNotes("실제 실행 산출물. outputs/paper-korean/fig_05_korean_cumulative_returns.png");
}

// =====================================================================
// S8  비용 및 강건성
// =====================================================================
{
  const s = slide("거래비용과 강건성 — 결론은 유지, 성과는 크게 축소", "2. 재현 결과");

  // left: cost
  s.addText("거래비용 5 bp + 공매도 보유비용 1 bp를 목적함수에 반영", {
    x: M, y: 1.58, w: 5.85, h: 0.3, fontSize: 14, bold: true, color: INK, fontFace: F, margin: 0,
  });
  const cost = [
    [hdr("지표"), hdr("비용 미반영"), hdr("비용 반영")],
    ["Sharpe ratio", "4.15", { text: "1.37", options: { bold: true } }],
    ["연수익률", "16.8%", "6.0%"],
    ["일별 turnover", "1.214", { text: "0.464", options: { bold: true } }],
  ];
  s.addTable(cost, {
    ...tableOpts([2.35, 1.75, 1.75]),
    x: M, w: 5.85, y: 1.95, rowH: 0.4, fontSize: 12, align: "center",
  });
  s.addText(
    "모형이 비용을 알고 학습하면 turnover를 62% 줄여 대응한다.\n원 논문도 IPCA 기준 Sharpe 4.16 → 0.94 ~ 1.24로 하락했다.",
    { x: M, y: 3.75, w: 5.85, h: 0.7, fontSize: 12, color: GRAY, fontFace: F, lineSpacing: 18, margin: 0 }
  );

  // right: robustness
  s.addText("강건성 점검", {
    x: 7.0, y: 1.58, w: 5.68, h: 0.3, fontSize: 14, bold: true, color: INK, fontFace: F, margin: 0,
  });
  const rob = [
    [hdr("사양"), hdr("Sharpe"), hdr("원 논문과")],
    ["기준 (30일 lookback)", "4.15", "—"],
    ["60일 lookback", "3.45", "일치"],
    ["고정 모형 (재학습 없음)", "4.15", "일치"],
    ["5일 보유 목적함수", "3.11", "일치"],
    ["OU + FFN (신호 고정)", "1.88", "일치"],
    ["직접 FFN (신호 없음)", "2.19", "일치"],
  ];
  s.addTable(rob, {
    ...tableOpts([2.75, 1.35, 1.58]),
    x: 7.0, w: 5.68, y: 1.95, rowH: 0.335, fontSize: 11.5, align: "center",
  });
  s.addText("배분만 유연하게 한 두 ablation이 모두 기준에 크게 못 미친다.\n‘신호가 결정적’이라는 원 논문의 핵심 주장이 한국에서도 성립한다.", {
    x: 7.0, y: 4.35, w: 5.68, h: 0.7, fontSize: 12, color: GRAY, fontFace: F, lineSpacing: 18, margin: 0,
  });

  // bottom band
  s.addShape(pres.ShapeType.rect, { x: M, y: 5.3, w: CW, h: 1.2, fill: { color: BAND }, line: { color: BAND } });
  s.addText("원 논문과 다르게 나온 점", {
    x: M + 0.3, y: 5.42, w: 3.2, h: 0.3, fontSize: 12.5, bold: true, color: INK, fontFace: F, margin: 0,
  });
  s.addText(
    [
      { text: "①  원 수익률(K = 0) 성과가 음수          ②  단순 반전 전략이 모든 lag에서 음수 (미국은 양수)", options: { breakLine: true } },
      { text: "③  상위 비중만 남기는 sparsification의 이득 없음          ④  K = 15에서 성과 하락 (미국은 평탄)" },
    ],
    { x: M + 0.3, y: 5.76, w: CW - 0.6, h: 0.62, fontSize: 11.5, color: GRAY, fontFace: F, lineSpacing: 17, margin: 0 }
  );
  note(s, "PCA5 잔차, CNN + Transformer 기준.  turnover는 연속 두 시점 비중벡터 차이의 L1 노름.", 6.65);
  s.addNotes("비용 반영 후 1.37이 실질적 결론. 4.15는 마찰 없는 상한.");
}

// =====================================================================
// S9  질문 1 — 표본
// =====================================================================
{
  const s = slide("논의 1 — 잔차 표본과 표본외 기간을 얼마나 늘려야 합니까?", "3. 논의사항");

  const data = [
    [hdr(""), hdr("원 논문 (미국)"), hdr("현재 (한국)"), hdr("확보 가능 최대")],
    ["원자료", "1978 – 2016", "2015-01 – 2026-07", "2015-01 – 2026-07"],
    ["잔차 표본", "1998 – 2016  (19년)", "2020-01 – 2026-07  (1,606일)", "2016 – 2026  (추정 약 10년)"],
    ["정책 OOS", { text: "2002 – 2016  (15년)", options: { bold: true } }, { text: "2024-01 – 2026-07  (2.4년)", options: { bold: true } }, { text: "약 6 – 7년", options: { bold: true } }],
  ];
  s.addTable(data, { ...tableOpts([1.9, 3.3, 3.6, 3.23]), y: 1.6, rowH: 0.44, fontSize: 12 });

  s.addText("여쭙고 싶은 것", {
    x: M, y: 3.75, w: CW, h: 0.32, fontSize: 15, bold: true, color: INK, fontFace: F, margin: 0,
  });
  s.addText(
    [
      { text: "표본외 2.4년으로 학위논문의 주장을 세울 수 있습니까?  최소 몇 년을 확보해야 한다고 보십니까?", options: { bullet: true, breakLine: true } },
      { text: "잔차 표본 시작을 2020년에서 2016년으로 당기면 OOS가 약 6~7년으로 늘어납니다.  다만 학습창 1,000일과 125일 재학습 계약을 유지하면 전 구간 재실행이 필요합니다.  진행할까요?", options: { bullet: true, breakLine: true } },
      { text: "2015년 이전 일별 자료 확보에 시간을 투자할 가치가 있습니까?  아니면 현재 구간에서 분석의 깊이를 더하는 편이 낫습니까?", options: { bullet: true } },
    ],
    { x: M, y: 4.15, w: CW, h: 1.9, fontSize: 13, color: INK, fontFace: F, paraSpaceAfter: 11, margin: 0 }
  );
  note(s, "보유 원자료 : 국내 수정주가 일별 8,651,872행 · 4,962종목 · 2015-01-02 ~ 2026-07-20.", 6.45);
  s.addNotes("핵심 질문. OOS 길이가 짧으면 t-통계량이 커도 설득력이 떨어진다는 점을 스스로 먼저 말할 것.");
}

// =====================================================================
// S10  질문 2 — 수익률 정의
// =====================================================================
{
  const s = slide("논의 2 — 현금배당을 제외한 price return을 사용해도 됩니까?", "3. 논의사항");

  const data = [
    [hdr(""), hdr("원 논문"), hdr("본 연구 현재")],
    ["수익률 정의", "CRSP total return", "권리·분할 조정 price return"],
    ["현금배당", "포함", { text: "제외", options: { bold: true } }],
    ["상장폐지 수익률", "포함", { text: "미확보", options: { bold: true } }],
  ];
  s.addTable(data, { ...tableOpts([2.6, 4.7, 4.73]), y: 1.6, rowH: 0.42, fontSize: 12 });

  s.addText("예상되는 영향", {
    x: M, y: 3.55, w: 5.85, h: 0.3, fontSize: 14, bold: true, color: INK, fontFace: F, margin: 0,
  });
  s.addText(
    [
      { text: "롱숏 잔차 전략이라 배당의 시장 전체 효과는 상당 부분 상쇄된다.", options: { bullet: true, breakLine: true } },
      { text: "그러나 배당락일 전후에 잔차가 체계적으로 왜곡될 수 있다.", options: { bullet: true, breakLine: true } },
      { text: "고배당 종목이 지속적으로 저평가 잔차로 잡힐 가능성이 있다.", options: { bullet: true } },
    ],
    { x: M, y: 3.92, w: 5.85, h: 1.5, fontSize: 12, color: GRAY, fontFace: F, paraSpaceAfter: 8, margin: 0 }
  );

  s.addText("여쭙고 싶은 것", {
    x: 7.0, y: 3.55, w: 5.68, h: 0.3, fontSize: 14, bold: true, color: INK, fontFace: F, margin: 0,
  });
  s.addText(
    [
      { text: "price return 기준으로 논문을 진행해도 됩니까?  아니면 total return이 필수 조건입니까?", options: { bullet: true, breakLine: true } },
      { text: "필수라면 배당 원자료 확보를 다른 작업보다 우선해야 합니까?", options: { bullet: true, breakLine: true } },
      { text: "배당락 조정 sensitivity 분석을 덧붙이는 것으로 충분한 방어가 됩니까?", options: { bullet: true } },
    ],
    { x: 7.0, y: 3.92, w: 5.68, h: 1.8, fontSize: 12.5, color: INK, fontFace: F, paraSpaceAfter: 10, margin: 0 }
  );
  note(s, "현재 결과는 모두 price return 기준이므로 원 논문의 total-return 경제성과 직접 비교되지 않습니다.", 6.45);
  s.addNotes("배당 제외가 결과를 과대/과소 어느 쪽으로 왜곡하는지 방향을 단정하지 말 것.");
}

// =====================================================================
// S11  질문 3 — IPCA characteristics
// =====================================================================
{
  const s = slide("논의 3 — IPCA에 쓸 팩터와 기업특성을 무엇으로 정할까요?", "3. 논의사항");

  s.addText("원 논문은 Chen et al. (2022)의 46개 기업특성을 240개월 rolling window로 사용해 조건부 잠재팩터를 추정합니다.", {
    x: M, y: 1.55, w: CW, h: 0.32, fontSize: 13, color: GRAY, fontFace: F, margin: 0,
  });

  const data = [
    [hdr("쟁점"), hdr("현재 상태"), hdr("선택지")],
    ["특성 집합", "미국 46개 정의를 그대로 이식해 builder 구현\n(427,076 종목-월 산출)", "미국 46개 유지  /  한국 문헌에서 검증된 집합으로 축소·대체"],
    ["일부 특성의 원천", "Spread · Beta 계열 · CF · NI 는 문서화된 proxy", "proxy 유지  /  해당 특성 제외  /  원천 확보"],
    ["시점 정렬", "실제 공시일 vintage 없음 → 회계연도 말 + 3개월 고정 lag", "고정 lag 유지  /  공시일 자료 확보"],
    ["표본 길이", "논문은 240개월 필요, 국내 월별 패널은 139개월", "window 완화 후 sensitivity로 표기  /  240개월 확보까지 보류"],
    ["국내 팩터와의 정합", "한국 FF5 + MOM은 별도 방법론으로 산출", "IPCA 특성과 정의·리밸런싱을 통일  /  분리 유지"],
  ];
  s.addTable(data, { ...tableOpts([1.95, 4.9, 5.18]), y: 2.0, rowH: 0.62, fontSize: 11.5 });

  s.addText(
    [
      { text: "여쭙고 싶은 것 : ", options: { bold: true } },
      { text: "특성 집합을 미국 정의 그대로 가져가는 것과 한국 시장에서 검증된 특성으로 재구성하는 것 중 어느 쪽이 심사에서 방어하기 좋습니까?  그리고 240개월 window 완화를 한계로 명시하고 진행해도 됩니까?" },
    ],
    { x: M, y: 5.75, w: CW, h: 0.85, fontSize: 12.5, color: INK, fontFace: F, lineSpacing: 19, margin: 0 }
  );
  note(s, "IPCA는 원 논문에서 가장 높은 성과를 낸 잔차 계열이므로 재현 완결성에 필수입니다.", 6.75);
  s.addNotes("IPCA는 반드시 한다는 전제. 질문은 '무엇으로 하느냐'.");
}

pres.writeFile({ fileName: OUT }).then(() => console.log("WROTE " + OUT));
