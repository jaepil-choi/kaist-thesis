// ============================================
// KAIST Thesis Template for Typst
// Converted from kaist-ucs.cls LaTeX template
// ============================================
//
// Based on KAIST thesis template v0.4
// Original LaTeX template by Chae, Seungbyung
// Converted to Typst by Claude Code
//
// Supports: Master's and Ph.D. theses
// Languages: Korean and English


// ============================================
// 1. UTILITY FUNCTIONS
// ============================================

// Format Korean date (YYYY년 MM월 DD일)
#let format-date-ko(year, month, day) = {
  [#(year)년 #(month)월 #(day)일]
}

// Format English date (Month DD, YYYY)
#let format-date-en(year, month, day) = {
  let months = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
  )
  [#months.at(month - 1) #day, #year]
}

// Get degree name in Korean
#let get-degree-name-ko(degree) = {
  if degree == "doctor" {
    "박 사 학 위 논 문"
  } else {
    "석 사 학 위 논 문"
  }
}

// Get degree name in English
#let get-degree-name-en(degree) = {
  if degree == "doctor" {
    "Ph.D. Dissertation"
  } else {
    "Master's Thesis"
  }
}

// Get academic degree name for submission page
#let get-academic-degree(degree, field) = {
  if degree == "doctor" {
    "Doctor of Philosophy"
  } else {
    if field == "science" {
      "Master of Science"
    } else if field == "engineering" {
      "Master of Science"
    } else if field == "business" {
      "Master of Business Administration"
    } else {
      "Master of Science"
    }
  }
}

// Get degree code prefix
#let get-degree-code(degree) = {
  if degree == "doctor" { "D" } else { "M" }
}


// ============================================
// 2. DEPARTMENT DATA
// ============================================

// Department codes and names
// Full list from department_names.tex
#let departments = (
  // Physical Sciences
  PH: (
    ko: "물리학과",
    en: "Department of Physics",
    en-academic: "Physics",
    code: "PH"
  ),
  MAS: (
    ko: "수리과학과",
    en: "Department of Mathematical Sciences",
    en-academic: "Mathematical Sciences",
    code: "MAS"
  ),
  CH: (
    ko: "화학과",
    en: "Department of Chemistry",
    en-academic: "Chemistry",
    code: "CH"
  ),
  BS: (
    ko: "생명과학과",
    en: "Department of Biological Sciences",
    en-academic: "Biological Sciences",
    code: "BS"
  ),

  // Engineering
  ME: (
    ko: "기계공학과",
    en: "Department of Mechanical Engineering",
    en-academic: "Mechanical Engineering",
    code: "ME"
  ),
  EE: (
    ko: "전기 및 전자공학부",
    en: "School of Electrical Engineering",
    en-academic: "Electrical Engineering",
    code: "EE"
  ),
  CS: (
    ko: "전산학부",
    en: "School of Computing",
    en-academic: "Computing",
    code: "CS"
  ),
  CBE: (
    ko: "생명화학공학과",
    en: "Department of Chemical and Biomolecular Engineering",
    en-academic: "Chemical and Biomolecular Engineering",
    code: "CBE"
  ),
  MS: (
    ko: "신소재공학과",
    en: "Department of Materials Science and Engineering",
    en-academic: "Materials Science and Engineering",
    code: "MS"
  ),
  CE: (
    ko: "건설 및 환경공학과",
    en: "Department of Civil and Environmental Engineering",
    en-academic: "Civil and Environmental Engineering",
    code: "CE"
  ),
  AE: (
    ko: "항공우주공학과",
    en: "Department of Aerospace Engineering",
    en-academic: "Aerospace Engineering",
    code: "AE"
  ),
  NQE: (
    ko: "원자력 및 양자공학과",
    en: "Department of Nuclear and Quantum Engineering",
    en-academic: "Nuclear and Quantum Engineering",
    code: "NQE"
  ),
  IE: (
    ko: "산업 및 시스템공학과",
    en: "Department of Industrial and Systems Engineering",
    en-academic: "Industrial and Systems Engineering",
    code: "IE"
  ),

  // Graduate Schools
  BTM: (
    ko: "기술경영전문대학원",
    en: "Graduate School of Innovation and Technology Management",
    en-academic: "Business and Technology Management",
    code: "BTM"
  ),
  KM: (
    ko: "경영학과",
    en: "Department of Management Engineering",
    en-academic: "KAIST MBA",
    code: "KM"
  ),
)

// Get department name
#let get-dept-name(code, lang) = {
  let dept = departments.at(code, default: none)
  if dept == none {
    return if lang == "korean" { "학과" } else { "Department" }
  }
  if lang == "korean" { dept.ko } else { dept.en }
}

// Get academic field name
#let get-dept-academic(code) = {
  let dept = departments.at(code, default: none)
  if dept == none { return "Science" }
  dept.en-academic
}


// ============================================
// 3. FRONT MATTER PAGE GENERATORS
// ============================================

// 3.1 Front Cover Page
#let make-front-cover(
  degree,
  title-ko,
  title-en,
  year,
  author-ko,
  author-cn,
  author-en,
) = {
  set page(
    numbering: none,
    header: none,
    footer: none,
  )

  set align(center)

  // Minipage 1: Degree names (10mm height)
  block(height: 10mm, width: 100%, above: 0pt, below: 0pt)[
    #v(1fr)
    #text(17pt)[#get-degree-name-ko(degree)]
    #linebreak()
    #text(15pt)[#get-degree-name-en(degree)]
  ]

  // Vertical space: 40mm
  v(40mm, weak: false)

  // Minipage 2: Titles and year (80mm height)
  block(height: 80mm, width: 100%, above: 0pt, below: 0pt)[
    #text(21pt)[#title-ko]
    #v(21pt, weak: false)
    #text(18pt)[#title-en]
    #v(18pt, weak: false)
    #text(18pt)[#str(year)]
  ]

  // Vertical space: 40mm
  v(40mm, weak: false)

  // Minipage 3: Author (70mm height, center-aligned)
  block(height: 70mm, width: 100%, above: 0pt, below: 0pt)[
    #v(1fr)
    #text(20pt)[#author-ko.family #h(0.5mm) #author-ko.given #h(1mm)]
    #text(18pt)[(#author-cn.family #h(0.5mm) #author-cn.given #h(1mm) #author-en.family, #author-en.given)]
    #v(25mm, weak: false)
    #text(20pt)[한 국 과 학 기 술 원]
    #v(1fr)
  ]

  // Vertical space: -5mm (negative!)
  v(-5mm, weak: false)

  // Minipage 4: Institution English (0mm height)
  block(height: 0mm, width: 100%, above: 0pt, below: 0pt)[
    #text(18pt)[Korea Advanced Institute of Science and Technology]
  ]

  pagebreak()
}

// 3.2 Inner Title Page
#let make-title-page(
  degree,
  title-ko,
  year,
  author-ko,
  dept-code,
  field,
) = {
  set page(
    numbering: none,
    header: none,
    footer: none,
  )

  set align(center)

  // Minipage 1: Degree type (12mm height)
  block(height: 12mm, width: 100%, above: 0pt, below: 0pt)[
    #v(1fr)
    #text(17pt)[#get-degree-name-ko(degree)]
  ]

  // Vertical space: 30mm
  v(30mm, weak: false)

  // Minipage 2: Title and year (70mm height)
  block(height: 70mm, width: 100%, above: 0pt, below: 0pt)[
    #text(21pt)[#title-ko]
    #v(38pt, weak: false)
    #text(18pt)[#str(year)]
  ]

  // Vertical space: 40mm
  v(40mm, weak: false)

  // Minipage 3: Author, institution, department (85mm height, center-aligned)
  block(height: 85mm, width: 100%, above: 0pt, below: 0pt)[
    #v(1fr)
    #text(20pt)[#author-ko.family #h(0.5mm) #author-ko.given]
    #v(27mm, weak: false)
    #text(20pt)[한 국 과 학 기 술 원]
    #v(7mm, weak: false)
    #text(20pt)[#get-dept-name(dept-code, "korean")]
    #v(1fr)
  ]

  pagebreak()
}

// 3.3 Approval Page (Korean)
#let make-approval-page-ko(
  degree,
  title-ko,
  author-ko-cont,
  committee,
  referee-year,
  referee-month,
  referee-day,
) = {
  set page(
    numbering: none,
    header: none,
    footer: none,
  )

  set align(center)

  // Minipage 1: Title (80mm height, center-aligned)
  block(height: 80mm, width: 100%, above: 0pt, below: 0pt)[
    #v(1fr)
    #text(21pt)[#title-ko]
    #v(1fr)
  ]

  // Vertical space: -10mm (negative!)
  v(-10mm, weak: false)

  // Minipage 2: Author (0mm height)
  block(height: 0mm, width: 100%, above: 0pt, below: 0pt)[
    #text(16pt)[#author-ko-cont.family#author-ko-cont.given]
  ]

  // Vertical space: 0mm
  v(0mm, weak: false)

  // Minipage 3: Approval statement (60mm height, center-aligned)
  block(height: 60mm, width: 100%, above: 0pt, below: 0pt)[
    #v(1fr)
    #text(16pt)[
      위 논문은 한국과학기술원 #if degree == "master" [석사학위논문으로] else [박사학위논문으로] \
      학위논문 심사위원회의 심사를 통과하였음
    ]
    #v(1fr)
  ]

  // Vertical space: 13mm
  v(13mm, weak: false)

  // Minipage 4: Date and committee (auto height to prevent overlap)
  block(width: 100%, above: 0pt, below: 0pt)[
    #set align(center)

    // Date
    #text(size: 16pt)[#format-date-ko(referee-year, referee-month, referee-day)]

    #v(30pt, weak: false)

    // Committee members using table
    #table(
      columns: (auto, auto, auto),
      stroke: none,
      row-gutter: 15pt,
      column-gutter: 10mm,
      align: (right, center, left),

      text(size: 16pt)[심사위원장], text(size: 16pt)[#committee.at(0)], text(size: 16pt)[(인)],
      text(size: 16pt)[심 사 위 원], text(size: 16pt)[#committee.at(1)], text(size: 16pt)[(인)],
      text(size: 16pt)[심 사 위 원], text(size: 16pt)[#committee.at(2)], text(size: 16pt)[(인)],
    )
  ]

  pagebreak()
}

// 3.4 Submission Approval Page (English)
#let make-submission-page(
  degree,
  title-en,
  author-en,
  dept-code,
  field,
  advisor-en,
  advisor-info,
  approval-year,
  approval-month,
  approval-day,
  grad-year,
) = {
  set page(
    numbering: none,
    header: none,
    footer: none,
  )

  set align(center)

  // Minipage 1: Title (30mm height)
  block(height: 30mm, width: 100%, above: 0pt, below: 0pt)[
    #v(1fr)
    #text(20pt)[#title-en]
    #v(1fr)
  ]

  // Vertical space: 10mm
  v(10mm, weak: false)

  // Minipage 2: Author (3mm height)
  block(height: 3mm, width: 100%, above: 0pt, below: 0pt)[
    #v(1fr)
    #text(14pt)[#author-en.given #author-en.family]
    #v(1fr)
  ]

  // Vertical space: 10mm
  v(10mm, weak: false)

  // Minipage 3: Advisor (8mm height with vfill - bottom aligned)
  block(height: 8mm, width: 100%, above: 0pt, below: 0pt)[
    #v(1fr)
    #text(14pt)[Advisor: #advisor-en]
  ]

  // Vertical space: 10mm
  v(10mm, weak: false)

  // Minipage 4: Submission text (no fixed height - let content determine)
  // Note: LaTeX has [45mm] but content doesn't fill it, creating unwanted space
  text(14pt)[
    A dissertation submitted to the faculty of \
    Korea Advanced Institute of Science and Technology in \
    partial fulfillment of the requirements for the degree of \
    #get-academic-degree(degree, field) in #get-dept-academic(dept-code)
  ]

  // Vertical space: 10mm
  v(10mm, weak: false)

  // Minipage 5: Signature section (0mm+ height)
  block(width: 100%, above: 0pt, below: 0pt)[
    #text(14pt)[
      Daejeon, Korea \
      #format-date-en(approval-year, approval-month, approval-day)
    ]

    #v(24pt, weak: false)

    #text(size: 14pt)[Approved by]

    #v(18mm, weak: false)

    // Signature section - center-aligned line (LaTeX \makebox in center environment)
    #show line: set block(below: 0pt, above: 0pt)
    #line(length: 50%, stroke: 0.5pt)
    #linebreak()
    #text(size: 14pt)[#advisor-en]
    #linebreak()
    #text(size: 14pt)[#advisor-info]

    #v(20mm, weak: false)

    // Ethics statement with footnote marker (center-aligned in LaTeX)
    #text(size: 12pt)[The study was conducted in accordance with Code of Research Ethics#super[1].]
  ]

  // Place footnote at bottom of page with separator line (left-aligned, justified text)
  place(
    bottom,
    dx: 0pt,
    dy: -10pt,
    [
      #set align(left)
      #set par(justify: true)
      #line(length: 30%, stroke: 0.4pt)
      #v(3pt)
      #text(size: 10pt)[
        #super[1]Declaration of Ethical Conduct in Research: I, as a graduate student of KAIST, hereby declare that I have not committed any acts that may damage the credibility of my research. These include, but are not limited to: falsification, thesis written by someone else, distortion of research findings or plagiarism. I confirm that my dissertation contains honest conclusions based on my own careful research under the guidance of my thesis advisor.
      ]
    ]
  )

  pagebreak()
}

// 3.5 Thesis Information Page
#let make-thesis-info(
  degree,
  dept-code,
  author-ko-cont,
  title-ko,
  grad-year,
  advisor-ko-cont,
  language,
) = {
  // Two-column layout: left (30mm) and right (textwidth - 30mm)
  grid(
    columns: (30mm, 1fr),
    column-gutter: 0mm,
    row-gutter: 0pt,

    // Left column: Degree code
    align(left + horizon)[
      #text(14pt, weight: "bold", font: "Arial")[
        #get-degree-code(degree)#departments.at(dept-code).code
      ]
    ],

    // Right column: Thesis info (raised 3pt)
    align(left + horizon)[
      #move(dy: -3pt)[
        #set text(12pt, font: "Arial")
        #set par(leading: 0.5em)

        // Korean info line
        #author-ko-cont.family#author-ko-cont.given. #title-ko. #get-dept-name(dept-code, "korean"). #grad-year 년. 지도교수: #advisor-ko-cont. #if language == "korean" [(한글 논문)] else [(영문 논문)]

        #v(0.3em)

        // English info line
        #author-ko-cont.family, #author-ko-cont.given. #title-ko. #get-dept-name(dept-code, "english"). #grad-year. Advisor: #advisor-ko-cont. #if language == "korean" [(Text in Korean)] else [(Text in English)]
      ]
    ]
  )

  v(16pt)

  // Do NOT pagebreak here - abstracts go on the same page
}

// 3.6 Abstract Pages (Korean Summary + English Abstract)
#let make-abstract-pages(
  summary-ko,
  keywords-ko,
  abstract-en,
  keywords-en,
) = {
  // Korean Summary header (underlined and bold) - Batang doesn't support bold but use anyway
  underline[#text(weight: "bold")[초 록]]

  linebreak()

  // Korean summary text (NO first-line indent)
  set par(justify: true, first-line-indent: 0em, leading: 0.65em)
  summary-ko

  // Korean keywords (3mm space, underlined and bold header)
  v(3mm)
  underline[#text(weight: "bold")[핵 심 낱 말]]
  h(0.5em)
  keywords-ko.join(", ")

  // Space before English abstract
  v(9mm)

  // English Abstract header (underlined and bold)
  underline[#text(font: "Times New Roman", weight: "bold")[Abstract]]

  linebreak()

  // English abstract text (NO first-line indent)
  set par(justify: true, first-line-indent: 0em, leading: 0.65em)
  abstract-en

  // English keywords (3mm space, underlined and bold header)
  v(3mm)
  underline[#text(font: "Times New Roman", weight: "bold")[Keywords]]
  h(0.5em)
  keywords-en.join(", ")

  pagebreak()
}


// ============================================
// 4. MAIN TEMPLATE FUNCTION
// ============================================

#let thesis(
  // Degree and language
  degree: "master",        // "doctor" or "master"
  language: "korean",      // "korean" or "english"
  mode: "final",           // "final" or "draft"

  // Titles
  title-ko: none,
  title-en: none,

  // Author
  author-ko: (family: "", given: ""),        // With spaces: 안 진 현
  author-ko-cont: (family: "", given: ""),   // No spaces: 안 진현
  author-cn: (family: "", given: ""),        // Chinese: 安 眞 玄
  author-en: (family: "", given: ""),        // English: Ahn, Jin-Hyun

  // Department
  dept-code: "CS",
  field: "engineering",    // "science", "engineering", "business"

  // Student ID
  student-id: none,

  // Advisor
  advisor-ko: "",          // With spaces: 홍 길 동
  advisor-ko-cont: "",     // No spaces: 홍길동
  advisor-en: "",          // English: Gildong Hong
  advisor-info: "",        // Professor of ...

  // Co-advisor (optional)
  co-advisor-ko: none,
  co-advisor-ko-cont: none,
  co-advisor-en: none,

  // Committee
  committee: (),           // Array of 3 (master) or 5 (doctor) names

  // Dates
  approval-date: (year: 2024, month: 1, day: 1),
  referee-date: (year: 2024, month: 1, day: 1),
  grad-year: 2024,

  // Abstract
  summary-ko: [],
  keywords-ko: (),
  abstract-en: [],
  keywords-en: (),

  // Main document body
  doc,
) = {

  // ----------------------------------------
  // 4.1 Document-wide Settings
  // ----------------------------------------

  // Page setup
  set page(
    paper: "a4",
    margin: (
      left: 25.4mm,
      right: 25.4mm,
      top: 30mm,
      bottom: 25.4mm,
    ),
  )

  // Text settings
  set text(
    font: ("HCR Batang", "New Computer Modern"),
    size: 10pt,
    lang: if language == "korean" { "ko" } else { "en" },
  )

  // Paragraph settings
  set par(
    justify: true,
    leading: 0.65em,
    first-line-indent: 2em,
  )

  // Heading numbering
  set heading(numbering: "1.1")

  // ----------------------------------------
  // 4.2 Element Styling
  // ----------------------------------------

  // Chapter headings (Level 1)
  show heading.where(level: 1): it => {
    // Start new page for numbered chapters
    if it.numbering != none {
      pagebreak(weak: true)
    }

    set align(center)
    set text(14pt, weight: "bold")

    v(10pt)

    if it.numbering != none {
      // Check if this is an appendix (supplement is "Appendix")
      if it.supplement == [Appendix] {
        [Appendix #counter(heading).display(). #h(1em) #it.body]
      } else if language == "korean" {
        [제 #counter(heading).display() 장 #h(1em) #it.body]
      } else {
        [Chapter #counter(heading).display(). #h(1em) #it.body]
      }
    } else {
      it.body
    }

    v(20pt)
  }

  // Section headings (Level 2)
  show heading.where(level: 2): it => {
    set text(12pt, weight: "bold")
    v(8pt)
    it
    v(8pt)
  }

  // Subsection headings (Level 3)
  show heading.where(level: 3): it => {
    set text(11pt, weight: "bold")
    v(6pt)
    it
    v(6pt)
  }

  // ----------------------------------------
  // 4.3 Front Matter (Final mode only)
  // ----------------------------------------

  if mode == "final" {
    // Front cover
    make-front-cover(
      degree,
      title-ko,
      title-en,
      grad-year,
      author-ko,
      author-cn,
      author-en,
    )

    // Inner title page
    make-title-page(
      degree,
      title-ko,
      grad-year,
      author-ko,
      dept-code,
      field,
    )

    // Approval page (Korean)
    make-approval-page-ko(
      degree,
      title-ko,
      author-ko-cont,
      committee,
      referee-date.year,
      referee-date.month,
      referee-date.day,
    )

    // Submission approval (English)
    make-submission-page(
      degree,
      title-en,
      author-en,
      dept-code,
      field,
      advisor-en,
      advisor-info,
      approval-date.year,
      approval-date.month,
      approval-date.day,
      grad-year,
    )

    // Thesis info
    make-thesis-info(
      degree,
      dept-code,
      author-ko-cont,
      title-ko,
      grad-year,
      advisor-ko-cont,
      language,
    )

    // Abstract pages
    make-abstract-pages(
      summary-ko,
      keywords-ko,
      abstract-en,
      keywords-en,
    )
  }

  // ----------------------------------------
  // 4.4 Table of Contents
  // ----------------------------------------

  // Roman numerals for front matter
  set page(
    numbering: "i",
    number-align: center,
    footer: context {
      let num = counter(page).display("i")
      align(center)[-- #num --]
    }
  )

  // Table of contents
  outline(
    title: [#text(font: "Times New Roman", weight: "bold")[Contents]],
    depth: 3,
    indent: auto,
  )

  pagebreak()

  // List of tables
  outline(
    title: [#text(font: "Times New Roman", weight: "bold")[List of Tables]],
    target: figure.where(kind: table),
  )

  pagebreak()

  // List of figures
  outline(
    title: [#text(font: "Times New Roman", weight: "bold")[List of Figures]],
    target: figure.where(kind: image),
  )

  pagebreak()

  // ----------------------------------------
  // 4.5 Main Content
  // ----------------------------------------

  // Arabic numerals for main content
  set page(
    numbering: "1",
    number-align: center,
    footer: context {
      let num = counter(page).display("1")
      align(center)[-- #num --]
    }
  )
  counter(page).update(1)

  // Reset heading counter
  counter(heading).update(0)

  // Main document content
  doc
}
