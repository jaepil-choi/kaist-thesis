<#
.SYNOPSIS
    발표자료(.qmd)를 revealjs HTML로 렌더한다.

.DESCRIPTION
    Windows 사용자명이 한글이면 Quarto의 theme(SCSS) 컴파일이 실패한다.
    Quarto는 dart-sass 호출을 임시 .bat 파일에 UTF-8로 적어 cmd.exe로 실행하는데,
    cmd.exe는 그 파일을 시스템 ANSI 코드페이지(cp949)로 읽으므로 경로의 한글이 깨져
    "지정된 경로를 찾을 수 없습니다"로 끝난다.

    그래서 Quarto 설치 디렉터리를 C:\tmp 아래 ASCII junction으로 노출하고 임시·캐시
    디렉터리도 ASCII 경로로 돌린 뒤, 그 junction 안의 quarto.exe로 렌더한다.
    원본 설치는 건드리지 않는다. 자세한 내용은 corporate-windows skill의
    references/quarto.md 참고.

.EXAMPLE
    pwsh -File thesis/meetings/2026-08-24-advisor/render.ps1
#>

[CmdletBinding()]
param(
    [string]$Qmd = (Join-Path $PSScriptRoot 'advisor-meeting-guijarro-korea.qmd'),
    [string]$WorkRoot = 'C:\tmp'
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $Qmd)) { throw "qmd를 찾을 수 없다: $Qmd" }

$quarto = (Get-Command quarto -ErrorAction SilentlyContinue).Source
if (-not $quarto) { throw 'quarto를 PATH에서 찾을 수 없다.' }

# ...\Quarto\bin\quarto.cmd -> ...\Quarto
$quartoHome = Split-Path (Split-Path $quarto -Parent) -Parent

$nonAscii = '[^\u0000-\u007F]'
$needsWorkaround = ($quartoHome -match $nonAscii) -or ($env:TEMP -match $nonAscii)

if ($needsWorkaround) {
    Write-Host 'Quarto 설치 경로에 non-ASCII 문자가 있어 ASCII junction으로 우회한다.'

    $junction = Join-Path $WorkRoot 'quarto-ascii'
    $tmpDir = Join-Path $WorkRoot 'quarto-tmp'
    $cacheDir = Join-Path $WorkRoot 'quarto-appdata'

    if (-not (Test-Path -LiteralPath $junction)) {
        New-Item -ItemType Junction -Path $junction -Target $quartoHome | Out-Null
    }
    foreach ($d in @($tmpDir, $cacheDir)) {
        if (-not (Test-Path -LiteralPath $d)) { New-Item -ItemType Directory -Path $d -Force | Out-Null }
    }

    $quarto = Join-Path $junction 'bin\quarto.exe'
    if (-not (Test-Path -LiteralPath $quarto)) { throw "junction에서 quarto.exe를 찾을 수 없다: $quarto" }

    # 세션 임시 디렉터리와 sass 캐시도 ASCII여야 한다. junction만으로는 부족하다.
    $env:TMP = $tmpDir
    $env:TEMP = $tmpDir
    $env:LOCALAPPDATA = $cacheDir
}

Push-Location (Split-Path $Qmd -Parent)
try {
    & $quarto render (Split-Path $Qmd -Leaf)
    if ($LASTEXITCODE -ne 0) { throw "quarto render 실패 (exit $LASTEXITCODE)" }
}
finally {
    Pop-Location
}
