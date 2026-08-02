# PowerShell equivalent of _tools/hooks/pre-commit, for Windows without Git Bash.
#
# Git for Windows normally ships bash, so the sh hook works. But when it does not,
# or when python resolves to the Microsoft Store stub, the guardrail stops
# guarding silently - which is worse than not having it. Run this instead:
#
#   powershell -ExecutionPolicy Bypass -File _tools\hooks\pre-commit.ps1
#
# Or wire it as the hook itself:
#   git config core.hooksPath _tools/hooks
#   # then, if the sh hook fails on your machine, replace its body with:
#   #   exec powershell -ExecutionPolicy Bypass -File _tools/hooks/pre-commit.ps1

$ErrorActionPreference = 'Stop'

function Resolve-Python {
    foreach ($candidate in @('python', 'python3', 'py')) {
        $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($cmd) {
            # The Store stub answers to 'python' but cannot run anything.
            & $candidate -c "import sys; sys.exit(0)" 2>$null
            if ($LASTEXITCODE -eq 0) { return $candidate }
        }
    }
    Write-Host "[pre-commit] no working python found. Install Python 3.9+ and retry."
    exit 1
}

$py = Resolve-Python

function Invoke-Step {
    param([string]$Label, [string[]]$Arguments)
    Write-Host "[pre-commit] $Label"
    & $py @Arguments | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[pre-commit] blocked by $Label : run  $py $($Arguments -join ' ')"
        exit 1
    }
}

Invoke-Step 'front matter grammar' @('_tests/test_frontmatter.py')
Invoke-Step 'secret scanners'      @('_tests/test_secrets.py')
Invoke-Step 'linter self-test'     @('_tests/test_lint.py')
Invoke-Step 'templates + scaffold' @('_tests/test_templates.py')
Invoke-Step 'tools'                @('_tests/test_tools.py')
Invoke-Step 'scenario harness'     @('_tests/run_scenarios.py', '--self-test')
Invoke-Step 'enc_lint'             @('_tools/enc_lint.py')
Invoke-Step 'enc_lint _examples'   @('_tools/enc_lint.py', '--root', '_examples')
Invoke-Step 'enc_verify'           @('_tools/enc_verify.py')
Invoke-Step 'enc_bootstrap'        @('_tools/enc_bootstrap.py', '--check')

$staged = git diff --cached --name-only
foreach ($file in $staged) {
    if ($file -match '(^|/)\.env($|\.)|\.pem$|\.key$') {
        Write-Host "[pre-commit] blocked: a credential-looking file is staged ($file)"
        exit 1
    }
}

Write-Host '[pre-commit] OK'
