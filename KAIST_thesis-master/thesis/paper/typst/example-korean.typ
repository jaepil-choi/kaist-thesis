// ============================================
// KAIST Master's Thesis Example (Korean)
// Converted from sample_in_Korean.tex
// ============================================

#import "kaist-thesis.typ": thesis

#show: thesis.with(
  // Degree and language
  degree: "master",
  language: "english",
  mode: "final",

  // Titles
  title-ko: [탄소 나노튜브의 물리적 특성에 대한 이론 연구],
  title-en: [Theoretical Study on Physical Properties of Carbon Nanotubes],

  // Author information
  author-ko: (family: "안", given: "진 현"),
  author-ko-cont: (family: "안", given: "진현"),
  author-cn: (family: "安", given: "眞 玄"),
  author-en: (family: "Ahn", given: "Jin-Hyun"),

  // Department
  dept-code: "CS",
  field: "engineering",

  // Student ID
  student-id: "20100000",

  // Advisor
  advisor-ko: "홍 길 동",
  advisor-ko-cont: "홍길동",
  advisor-en: "Gildong Hong",
  advisor-info: "Professor of Computer Science",

  // Committee members (3 for Master's)
  committee: (
    "홍 길 동",
    "안 진 현",
    "정 태 성",
  ),

  // Dates
  approval-date: (year: 2020, month: 11, day: 30),
  referee-date: (year: 2020, month: 11, day: 30),
  grad-year: 2020,

  // Korean summary
  summary-ko: [
    지난 10여 년간 탄소 나노튜브는 자체의 독특한 전기적, 기계적 성질로
    인하여 다가오는 나노기술 분야의 이상적인 기초물질중의 하나로 떠오르고
    있다. 흑연을 감는 세세한 방법에 따라 전기적 특성이 금속성에서 1eV의
    띠간격을 가지는 반도체 특성까지 다양한 분포로 존재한다.
    본 학위논문에서는 탄소 나노튜브의 여러 물리적 성질에 대해 고찰하는데,
    기본적으로 제일원리 밀도함수 이론과 밀접결합근사 모형을 사용하여 전기적
    특성과 그 제어 방법, 자기적 특성, 그리고 수송특성 등을 다루고자 한다.
  ],
  keywords-ko: ("가", "나", "다"),

  // English abstract
  abstract-en: [
    For the last decade, carbon nanotubes have been emerging as one
    of ideal materials for the building block of the forthcoming
    nanotechnology, due to their unique electrical and mechanical
    properties. Depending on detailed wrapping-up methods, their
    electronic properties show a wide spectrum from metals to
    large-gap semiconductors with band gaps of 1eV.
    In this thesis, we study various physical properties of carbon
    nanotubes, including electrical properties and their controlling
    methods, magnetic properties, and transport characteristics,
    based on the first-principles density-functional theory and
    the tight-binding model.
  ],
  keywords-en: ("a", "b", "c"),
)

// ============================================
// MAIN CONTENT
// ============================================

= 머릿말

본문을 한글로 작성할 때 머릿말로 시작을 하시는 게 좋습니다. @FD1
인용은 다음과 같이 합니다 @RVP1 - @ML2.
인용은 뒤에 인용을 쓰는 칸이 있습니다. 참고하여서 인용하시길 바랍니다 @SOCA2, @EF2.
한글 논문에는 영어를 쓰지 마시기 바랍니다.

= 본문 작성

== 작성

장과 절 그리고 부절로 본문을 작성하실 수 있습니다.

=== 자동

이것들은 자동으로 차례에 들어가게 됩니다.

== 한글 논문

한글 논문에는 영어를 쓰지 마시기 바랍니다.

= 그림, 표

== 그림과 표를 본문에서 이야기하기

본문에서 그림과 표에 관해 이야기를 할 때도 인용에서처럼 하시면 됩니다.

// Table example
#figure(
  table(
    columns: (auto, auto, auto, auto, auto, auto, auto, auto, auto, auto, auto),
    align: center,
    stroke: (x, y) => {
      if y == 0 or y == 1 or y == 5 {
        (bottom: 1pt)
      } else if y == 6 {
        (bottom: 2pt)
      }
    },

    table.header(
      [], [], [BF], table.cell(colspan: 2)[SW-I], [], table.cell(colspan: 2)[SW-II], [SW-III], [CAP], [],
    ),
    [], [], [], [Para], [Ferro], [], [Para], [Ferro], [], [], [],
    [], [$E$ (eV)], [0], [7.796], [7.832], [], [10.418], [10.408], [11.5], [13.2], [],
    [], [$M$ ($mu_B$)], [0], [0], [1.94], [], [0], [2.06], [0], [0], [],
  ),
  caption: [표 제목을 넣으십시오.],
  kind: table,
) <mag-tab1>

// Figure example
#figure(
  image("sample-fig1.png", width: 12.5cm),
  caption: [그림 제목을 넣으십시오.],
) <mag-fig1>

= 맺음말

마지막은 맺음말로 하는 것을 권합니다.

// ============================================
// APPENDIX
// ============================================

#set heading(numbering: "A.1", supplement: [Appendix])
#counter(heading).update(0)

= Chapter Name

This is a chapter.

// ============================================
// BIBLIOGRAPHY
// ============================================

#set heading(numbering: none)

#pagebreak()

#bibliography("references.bib", title: "Bibliography", style: "ieee")

// ============================================
// ACKNOWLEDGMENT
// ============================================

#pagebreak()

#set par(first-line-indent: 2em, hanging-indent: 0em)
#set text(size: 10pt)

= 사 사 <acknowledgment>

언제나 저를 바른 길로 이끌어 주시는 송익호 교수님께 큰 고마움을 느낍니다.
끝으로 오늘의 제가 있을 수 있도록 사랑으로 키워 주신 가족들에게 감사드립니다.
저의 이 작은 결실이 그분들께 조금이나마 보답이 되기를 바랍니다.

// ============================================
// CURRICULUM VITAE
// ============================================

#pagebreak()

= 약 력 <cv>

#v(5mm)
#align(center)[#text(weight: "bold", size: 12pt)[개인 정보]]

#table(
  columns: (auto, 1fr),
  stroke: none,
  align: (right, left),
  row-gutter: 5pt,

  [성명:], [안 진 현],
  [생년월일:], [199x년 x월 xx일],
  [출생지:], [...],
  [주소:], [...],
)

#v(5mm)
#align(center)[#text(weight: "bold", size: 12pt)[학력]]

#list(
  indent: 1em,
  [2007. 3. -- 2009. 2. #h(1em) 고등학교 (2년 수료)],
  [2009. 2. -- 2013. 8. #h(1em) 한국과학기술원 수리과학과 (학사)],
  [2013. 9. -- 2016. 2. #h(1em) 한국과학기술원 수리과학과 (석사)],
)

#v(5mm)
#align(center)[#text(weight: "bold", size: 12pt)[경력]]

#list(
  indent: 1em,
  [2013. 9. -- 2016. 2. #h(1em) 한국과학기술원 수리과학과 일반조교],
)

#v(5mm)
#align(center)[#text(weight: "bold", size: 12pt)[연구 업적]]

#set par(first-line-indent: 0em, hanging-indent: 1.5em)

J. Ahn, _Analysis of Tail Probability of Interference at a Node in 2-dimensional Homogeneous Poisson Point Process_, Master Thesis, Korea Adv. Inst. Science, Techn., Daejeon, Republic of Korea, 2016.
