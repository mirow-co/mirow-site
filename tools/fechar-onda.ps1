<#
.SYNOPSIS
    Fecha uma onda com UM comando: cache-bust -> suite -> contact sheets ->
    deploy (com acompanhamento do Pages) -> verificacao da versao ao vivo.

.DESCRIPTION
    (issue mirow-marketing#195, alavanca F do aulao de tempos 2026-08-07)
    Antes deste script o fechamento eram 6 invocacoes manuais, cada uma com a
    sua espera. Aqui a sequencia roda emendada e para no primeiro erro.

    Uso:
        powershell -NoProfile -ExecutionPolicy Bypass -File tools/fechar-onda.ps1 `
            -Paginas pt/,pt/imprensa/
        powershell -NoProfile -ExecutionPolicy Bypass -File tools/fechar-onda.ps1 -DryRun

    O que ele NAO faz de proposito: commit do main (mensagem de commit e
    decisao do agente/consultor) e governanca no repo privado (issues/painel).

.PARAMETER Paginas
    Paginas-alvo dos contact sheets (relativas, ex.: pt/ pt/insights/).
    Default: pt/ (a home sempre entra).

.PARAMETER DryRun
    Roda tudo mas passa -DryRun ao deploy (nada e empurrado).

.PARAMETER SemSheets
    Pula os contact sheets (para ondas que nao tocam layout).
#>
[CmdletBinding()]
param(
    [string[]] $Paginas = @('pt/'),
    [switch] $DryRun,
    [switch] $SemSheets
)

$ErrorActionPreference = 'Stop'
$raiz = Split-Path -Parent $PSScriptRoot
$env:PYTHONIOENCODING = 'utf-8'

function Passo($txt) { Write-Host "`n#### $txt ####" -ForegroundColor Magenta }

Push-Location $raiz
try {
    # 1. cache-busting SEMPRE por ultimo entre os scripts de conteudo -- se a
    # VERSAO nao foi incrementada nesta onda, o proprio 27 reporta 0 mudancas
    # e o agente decide se era intencional (onda so de conteudo HTML).
    Passo '1/4 cache-busting (27 roda sempre por ultimo)'
    & python tools_onda6\27_cache_busting.py . | Select-Object -Last 3
    if ($LASTEXITCODE -ne 0) { throw 'cache-busting falhou' }

    # 2. contact sheets das paginas-alvo (P4 ampliada: nenhuma onda vira
    # "PRONTO" sem o sheet das paginas tocadas).
    if (-not $SemSheets) {
        Passo '2/4 contact sheets das paginas-alvo'
        # (o terminador "@ do here-string TEM que ficar na coluna 0)
        $py = @"
import sys, subprocess
sys.path.insert(0, 'tools')
from verificacoes import ServidorLocal
paginas = sys.argv[1:]
with ServidorLocal('public') as srv:
    for p in paginas:
        r = subprocess.run([sys.executable, 'tools_onda6/qa/breakpoints.py',
                            srv.base() + '/' + p, 'aos-off'])
        if r.returncode not in (0, None):
            raise SystemExit('contact sheet com problema em ' + p)
"@
        & python -c $py @Paginas
        if ($LASTEXITCODE -ne 0) { throw 'contact sheet acusou problema -- ver _qa_breakpoints/' }
    } else {
        Passo '2/4 contact sheets: PULADOS (-SemSheets)'
    }

    # 3+4. deploy: ele mesmo roda a suite completa (gate), monta o gh-pages,
    # empurra e acompanha o build do Pages com retry (passo 7 do deploy.ps1).
    Passo '3/4 deploy (suite completa e o gate; Pages acompanhado com retry)'
    $argsDeploy = @()
    if ($DryRun) { $argsDeploy += '-DryRun' }
    & powershell -NoProfile -ExecutionPolicy Bypass -File tools\deploy.ps1 @argsDeploy
    if ($LASTEXITCODE -ne 0) { throw 'deploy falhou' }
    if ($DryRun) { Write-Host "`nDryRun completo -- nada foi ao ar." -ForegroundColor Yellow; return }

    # 4. verificacao ao vivo: a VERSAO carimbada tem que estar servida.
    Passo '4/4 versao ao vivo'
    $versao = (Select-String -Path tools_onda6\27_cache_busting.py -Pattern '^VERSAO = (\d+)').Matches[0].Groups[1].Value
    $alvo = "?v=$versao"
    $inicio = Get-Date
    while ($true) {
        if (((Get-Date) - $inicio).TotalMinutes -gt 6) {
            throw "site ao vivo ainda nao serve $alvo apos 6 min -- conferir na mao"
        }
        try {
            $html = (Invoke-WebRequest -UseBasicParsing 'https://mirow-co.github.io/mirow-site/pt/' -TimeoutSec 20).Content
            if ($html.Contains($alvo)) {
                Write-Host "NO AR: a home serve $alvo." -ForegroundColor Green
                break
            }
        } catch {}
        Start-Sleep -Seconds 15
    }
    Write-Host "`nFechamento tecnico OK. Falta (humano/agente): commit do main se ainda nao feito," -ForegroundColor Cyan
    Write-Host 'fechar as issues com evidencia e atualizar painel/BOARD no repo privado (P4).' -ForegroundColor Cyan
}
finally {
    Pop-Location
}
