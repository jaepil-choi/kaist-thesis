# Quarto under non-ASCII Windows paths

Use this when `quarto render` (or even `quarto check`) fails during theme or Sass compilation on a
machine whose Windows user profile contains non-ASCII characters.

## Symptom

Every format that compiles Sass fails, including a minimal document with no custom theme:

```
ERROR: Theme file compilation failed:

Stack trace:
    at processResult (.../quarto.js)
    at dartCommand (.../quarto.js)
    at async compileSass (.../quarto.js)
    at async revealTheme (.../quarto.js)
```

The error message body is empty. `quarto check` fails the same way at "Checking versions of quarto
binary dependencies". This is not a document problem, so do not edit the `.qmd` or the theme.

Recover the real error with `--log-level debug`:

```
[DART stderr] : 지정된 경로를 찾을 수 없습니다.
```

(cp949-mojibake in a UTF-8 terminal; the message is "The system cannot find the path specified.")

## Cause

Quarto's `safeWindowsExec` writes the dart-sass command line into a temporary `.bat` file with
`Deno.writeTextFileSync`, which encodes UTF-8, and then runs that file through `cmd.exe`. `cmd.exe`
reads a batch file using the system ANSI code page (cp949 on a Korean Windows install), so any
non-ASCII path inside the generated command line is mangled and the launch fails before dart-sass
ever starts.

Three separate paths reach that batch file, and **all three** must be ASCII:

| Path | Source | Default under a Korean username |
|---|---|---|
| `sass.bat` and the `--load-path=` resource directories | Quarto install dir | `%LOCALAPPDATA%\Programs\Quarto` |
| the generated `.scss` input | Quarto session temp dir | `%TEMP%\quarto-session*` |
| the compiled `.css` output | Quarto sass cache | `%LOCALAPPDATA%\quarto\sass` |

Fixing only one or two of them still fails. Verified: junction alone fails, junction + `TEMP`/`TMP`
fails, junction + `LOCALAPPDATA` fails. `APPDATA` is not involved.

## Workaround

Expose the whole Quarto installation through an ASCII junction, redirect the temp and cache
directories, and invoke `quarto.exe` from inside the junction. A junction needs no admin rights and
does not modify the installation.

```powershell
$quartoHome = "$env:LOCALAPPDATA\Programs\Quarto"
if (-not (Test-Path -LiteralPath 'C:\tmp\quarto-ascii')) {
    New-Item -ItemType Junction -Path 'C:\tmp\quarto-ascii' -Target $quartoHome | Out-Null
}
foreach ($d in @('C:\tmp\quarto-tmp', 'C:\tmp\quarto-appdata')) {
    if (-not (Test-Path -LiteralPath $d)) { New-Item -ItemType Directory -Path $d -Force | Out-Null }
}

$env:TMP = 'C:\tmp\quarto-tmp'
$env:TEMP = 'C:\tmp\quarto-tmp'
$env:LOCALAPPDATA = 'C:\tmp\quarto-appdata'

& 'C:\tmp\quarto-ascii\bin\quarto.exe' render report.qmd
```

Run this from the document's directory, or `Push-Location` into it, so relative resource paths in
the document still resolve. The document source, its output, and the working directory may stay on
a non-ASCII or non-`C:` path; only the three paths above must be ASCII.

Verify with a throwaway minimal document before blaming the real one:

```powershell
Set-Content -Path 'C:\tmp\qmin.qmd' -Value "---`nformat: revealjs`n---`n`n## a`n`nb"
```

If the minimal document also fails, the cause is environmental, not the document.

## Alternative without a junction

If a junction cannot be created, the same three paths can be redirected with environment variables
alone. This is more moving parts, so prefer the junction.

```powershell
$env:QUARTO_SHARE_PATH = 'C:\tmp\quarto-share'      # junction or copy of ...\Quarto\share
$env:QUARTO_DART_SASS  = 'C:\tmp\dart-sass\sass.bat' # copy of ...\bin\tools\x86_64\dart-sass
$env:TMP = $env:TEMP   = 'C:\tmp\quarto-tmp'
$env:LOCALAPPDATA      = 'C:\tmp\quarto-appdata'
```

When copying `dart-sass` into a shared directory such as `C:\tmp`, copy the whole folder (it holds
`sass.bat` plus `src\dart.exe` and `src\sass.snapshot`) to a uniquely named destination so
concurrent agents do not race on the same files.

## Guardrails

- Do not change the system code page or enable the Windows "Use Unicode UTF-8 for worldwide
  language support" beta option to work around this. That is a system-wide setting change with
  effects far beyond Quarto.
- Do not reinstall or move the Quarto installation.
- Do not assume every Quarto failure comes from the username. Preserve and inspect the original
  error, and confirm the Sass stack trace above, before applying this.
