# deploy-staging.ps1 - publica public/ no repo mirow-co/mirow-site-staging
# (Pages com dominio custom staging.mirow.com.br, noindex em toda pagina).
# NAO roda a suite completa - staging e ambiente de validacao, o gate duro
# continua sendo o tools/deploy.ps1 da producao.
# Uso: powershell -NoProfile -ExecutionPolicy Bypass -File tools/deploy-staging.ps1 [-DryRun]
# ASCII puro (regra dos .ps1 deste repo).

param([switch]$DryRun)

$ErrorActionPreference = "Stop"
$raiz = Split-Path -Parent $PSScriptRoot
$pub = Join-Path $raiz "public"
if (-not (Test-Path (Join-Path $pub ".nojekyll"))) { throw "public/.nojekyll nao encontrado - raiz errada?" }

$tmp = Join-Path $env:TEMP ("staging-" + [guid]::NewGuid().ToString("N").Substring(0,8))
New-Item -ItemType Directory -Path $tmp | Out-Null
# Onda 66: dizer O QUE esta sendo publicado. O staging recebe branch de trabalho
# (a reconstrucao fluida), e antes disso nada no log dizia de onde a arvore vinha.
$br = (git -C $raiz rev-parse --abbrev-ref HEAD).Trim()
$vs = (Select-String -Path (Join-Path $raiz "tools_onda6_cache_busting.py") -Pattern "^VERSAO = (\d+)").Matches[0].Groups[1].Value
Write-Host ("[0/4] branch: " + $br + " | VERSAO de cache: v=" + $vs) -ForegroundColor Cyan
Write-Host "[1/4] Copiando public/ para $tmp ..."
robocopy $pub $tmp /E /NFL /NDL /NJH /NJS | Out-Null
if ($LASTEXITCODE -ge 8) { throw "robocopy falhou ($LASTEXITCODE)" }
$global:LASTEXITCODE = 0

Write-Host "[2/4] Injetando noindex + robots.txt + CNAME (python)..."
$py = @'
import io, os, re, sys
raiz = sys.argv[1]
n = 0
for dirpath, _, files in os.walk(raiz):
    if os.sep + ".git" in dirpath: continue
    for f in files:
        if not f.endswith(".html"): continue
        p = os.path.join(dirpath, f)
        h = io.open(p, encoding="utf-8").read()
        novo = re.sub(r"<meta name=.robots. content=.[^\"']*.\s*/?>",
                      "<meta name='robots' content='noindex, nofollow' />", h)
        if novo == h and "noindex" not in h:
            novo = h.replace("<head>", "<head><meta name='robots' content='noindex, nofollow' />", 1)
        if novo != h:
            io.open(p, "w", encoding="utf-8", newline="").write(novo)
            n += 1
io.open(os.path.join(raiz, "robots.txt"), "w", encoding="utf-8", newline="").write(
    "User-agent: *\nDisallow: /\n")
sm = os.path.join(raiz, "sitemap.xml")
if os.path.exists(sm): os.remove(sm)
io.open(os.path.join(raiz, "CNAME"), "w", encoding="utf-8", newline="").write(
    "staging.mirow.com.br\n")
print("noindex em %d paginas" % n)
'@
$pyfile = Join-Path $tmp "_inject.py"
Set-Content -Path $pyfile -Value $py -Encoding utf8
python $pyfile $tmp
if ($LASTEXITCODE -ne 0) { throw "injecao de noindex falhou" }
Remove-Item $pyfile

Write-Host "[3/4] Commit e push para mirow-co/mirow-site-staging (branch main)..."
Push-Location $tmp
git init -q -b main
git remote add origin https://github.com/mirow-co/mirow-site-staging.git
git add -A
git commit -q -m "Staging build $(Get-Date -Format yyyy-MM-dd_HHmm) - espelho de public/ com noindex"
if ($DryRun) {
    Write-Host "DRYRUN: nao empurrado. Arvore em $tmp"
    Pop-Location
    exit 0
}
git push -f origin main
Pop-Location
Remove-Item -Recurse -Force $tmp

Write-Host "[4/4] Publicado. Conferir https://staging.mirow.com.br/pt/ apos o build do Pages (~1 min)."
