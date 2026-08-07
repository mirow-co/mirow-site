<#
.SYNOPSIS
    Publica o site: gh-pages passa a ser o conteudo EXATO de public/.

.DESCRIPTION
    Uso:
        powershell -NoProfile -ExecutionPolicy Bypass -File tools/deploy.ps1
        powershell -NoProfile -ExecutionPolicy Bypass -File tools/deploy.ps1 -DryRun
        powershell -NoProfile -ExecutionPolicy Bypass -File tools/deploy.ps1 -Rapido

    POR QUE ESTE ARQUIVO EXISTE
    ---------------------------
    O deploy antigo era um worktree permanente (mirow-site-gh) + uma junction
    (mirow-deploy-wrap) copiando a arvore de trabalho a mao. Isso gerou tres
    problemas: (1) 8 pastas paralelas em C:\dev, com risco de editar/testar a
    arvore errada; (2) o gh-pages virou editavel a mao, divergindo do main; e
    (3) copiava o DISCO em vez do git, o que escondeu por semanas que o
    .gitignore engolia 4 arquivos de public/wp-includes/js/dist/ -- num clone
    novo o site quebraria.

    Agora o gh-pages e ARTEFATO DE BUILD, reproduzivel a partir do main:
      * roda a suite tools/verificacoes.py e ABORTA se qualquer assercao falhar;
      * monta o commit do gh-pages via plumbing do git (index temporario), sem
        criar pasta nenhuma no disco -- nao ha o que esquecer de limpar;
      * confere que a arvore publicada e identica a public/ antes de empurrar.

.PARAMETER DryRun
    Roda a suite e monta o commit, mas NAO empurra. Mostra o diff contra o
    gh-pages atual.

.PARAMETER Rapido
    Passa --rapido para a suite (so assercoes estaticas, sem Chrome). Use apenas
    para iterar; o deploy de verdade roda a suite inteira.

.PARAMETER Mensagem
    Mensagem do commit do gh-pages.
#>
[CmdletBinding()]
param(
    [switch] $DryRun,
    [switch] $Rapido,
    [string] $Mensagem,
    # Nao acompanhar o build do Pages apos o push (volta ao comportamento
    # antigo: push e fim). O acompanhamento existe porque na onda 41 o build
    # veio "errored" por causa transitoria e ficou 30+ min sem ninguem ver --
    # 1 rebuild via API resolveu (issue mirow-marketing#195).
    [switch] $SemEspera
)

$ErrorActionPreference = 'Stop'

$raiz = Split-Path -Parent $PSScriptRoot
$pub  = Join-Path $raiz 'public'
if (-not (Test-Path $pub)) { throw "nao achei public/ em $raiz" }

function Passo($txt) { Write-Host "`n=== $txt ===" -ForegroundColor Cyan }

# ---------------------------------------------------------------- 1. sanidade
Passo '1/6 sanidade do repositorio'
Push-Location $raiz
try {
    $branch = (git rev-parse --abbrev-ref HEAD).Trim()
    Write-Host "branch: $branch"
    if ($branch -eq 'gh-pages') {
        throw 'nao rode o deploy com o gh-pages checkado -- ele e artefato de build, gerado do main'
    }
    $sujo = git status --porcelain -- public tools tools_onda6
    if ($sujo) {
        Write-Host 'ATENCAO: ha mudancas nao commitadas em public/tools:' -ForegroundColor Yellow
        $sujo | ForEach-Object { Write-Host "  $_" -ForegroundColor Yellow }
        Write-Host 'o gh-pages sai do DISCO, entao elas VAO ao ar mesmo sem commit.' -ForegroundColor Yellow
        Write-Host 'commite antes, para o main continuar reproduzindo o que esta publicado.' -ForegroundColor Yellow
        if (-not $DryRun) { throw 'arvore suja -- commite (ou use -DryRun) antes de publicar' }
    }

    # -------------------------------------------------------- 2. verificacoes
    Passo '2/6 suite de verificacoes (deploy bloqueia em falha)'
    $argsSuite = @((Join-Path $raiz 'tools\verificacoes.py'), $raiz)
    if ($Rapido) { $argsSuite += '--rapido' }
    & python @argsSuite
    if ($LASTEXITCODE -ne 0) {
        throw "DEPLOY BLOQUEADO: a suite de verificacoes falhou (codigo $LASTEXITCODE). Corrija antes de publicar."
    }

    # ------------------------------------------------ 3. montar a arvore
    # Plumbing de proposito: um index temporario descreve a arvore a publicar
    # sem materializar pasta nenhuma. `--work-tree=public` faz os caminhos do
    # commit ficarem relativos a public/ -- ou seja, gh-pages = public/ verbatim.
    Passo '3/6 montar a arvore do gh-pages a partir de public/'
    $indice = Join-Path ([System.IO.Path]::GetTempPath()) ("ghpages-idx-" + [guid]::NewGuid().ToString('N'))
    $env:GIT_INDEX_FILE = $indice
    try {
        # -f ignora o .gitignore da raiz: dentro de public/ nada e opcional.
        git --work-tree="$pub" add -A -f -- .
        if ($LASTEXITCODE -ne 0) { throw 'git add da arvore de publicacao falhou' }
        $tree = (git write-tree).Trim()
        Write-Host "tree: $tree"

        # ----------------------------------------- 4. conferir a arvore
        Passo '4/6 conferir que a arvore publicada e identica a public/'
        $noGit = @(git ls-tree -r --name-only $tree)
        $noDisco = @(Get-ChildItem -Path $pub -Recurse -File -Force |
            ForEach-Object { $_.FullName.Substring($pub.Length + 1).Replace('\', '/') })
        $soGit   = @(Compare-Object $noGit $noDisco -PassThru | Where-Object { $_.SideIndicator -eq '<=' })
        $soDisco = @(Compare-Object $noGit $noDisco -PassThru | Where-Object { $_.SideIndicator -eq '=>' })
        Write-Host ("{0} arquivos na arvore . {1} no disco" -f $noGit.Count, $noDisco.Count)
        if ($soGit.Count -or $soDisco.Count) {
            $soGit   | ForEach-Object { Write-Host "  so na arvore: $_" -ForegroundColor Yellow }
            $soDisco | ForEach-Object { Write-Host "  so no disco:  $_" -ForegroundColor Yellow }
            throw 'a arvore a publicar difere de public/ -- abortado'
        }
        if (-not ($noGit -contains '.nojekyll')) {
            throw 'public/.nojekyll ausente da arvore -- o GitHub Pages ignoraria as pastas com _'
        }

        # ----------------------------------------- 5. commit no gh-pages
        Passo '5/6 commit no gh-pages'
        git fetch origin gh-pages --quiet
        $pai = (git rev-parse --verify --quiet refs/remotes/origin/gh-pages)
        if ($pai) { $pai = $pai.Trim() }
        $treeAtual = if ($pai) { (git rev-parse "$pai^{tree}").Trim() } else { '' }
        if ($tree -eq $treeAtual) {
            Write-Host 'nada a publicar: o gh-pages ja tem exatamente este conteudo.' -ForegroundColor Green
            return
        }
        if ($pai) {
            Write-Host 'diferencas contra o que esta no ar:'
            git diff --stat $treeAtual $tree
        }
        if (-not $Mensagem) {
            $sha = (git rev-parse --short HEAD).Trim()
            $Mensagem = "Deploy de public/ (main $sha)"
        }
        $args = @('commit-tree', $tree, '-m', $Mensagem)
        if ($pai) { $args += @('-p', $pai) }
        $commit = (& git @args).Trim()
        git update-ref refs/heads/gh-pages $commit
        Write-Host "commit: $commit"

        # ----------------------------------------- 6. push
        Passo '6/6 push'
        if ($DryRun) {
            Write-Host 'DryRun: nada empurrado. O ref local refs/heads/gh-pages foi atualizado;' -ForegroundColor Yellow
            Write-Host 'para descartar: git update-ref refs/heads/gh-pages origin/gh-pages' -ForegroundColor Yellow
            return
        }
        git push origin gh-pages
        if ($LASTEXITCODE -ne 0) { throw 'push do gh-pages falhou' }
        Write-Host ''
        Write-Host 'publicado. O GitHub Pages leva ~1 min para propagar.' -ForegroundColor Green

        # ------------------------------- 7. acompanhar o build do Pages
        # (#195, alavanca C) Na onda 41 o build veio "errored" por causa
        # transitoria e a espera morta custou ~30 min. Aqui: espera o build
        # do commit empurrado terminar; se falhar, dispara UM rebuild via API
        # e espera de novo. Nao substitui a conferencia ao vivo -- a encurta.
        if ($SemEspera) {
            Write-Host 'CONFIRME AO VIVO antes de dizer NO AR:' -ForegroundColor Green
            Write-Host '  https://mirow-co.github.io/mirow-site/pt/' -ForegroundColor Green
            return
        }
        Passo '7/7 acompanhar o build do GitHub Pages'
        $repoApi = 'repos/mirow-co/mirow-site/pages/builds'
        $tentouRebuild = $false
        $inicio = Get-Date
        while ($true) {
            if (((Get-Date) - $inicio).TotalMinutes -gt 10) {
                Write-Host 'Pages ainda nao concluiu em 10 min -- confira depois com:' -ForegroundColor Yellow
                Write-Host "  gh api $repoApi/latest --jq .status" -ForegroundColor Yellow
                break
            }
            Start-Sleep -Seconds 15
            $st = (& gh api "$repoApi/latest" --jq '.status' 2>$null)
            if ($LASTEXITCODE -ne 0) { continue }
            $st = "$st".Trim()
            if ($st -eq 'built') {
                Write-Host 'Pages: build concluido.' -ForegroundColor Green
                break
            }
            if ($st -eq 'errored') {
                if ($tentouRebuild) {
                    throw 'Pages falhou DUAS vezes -- nao e transitorio; investigue (gh api ' + $repoApi + '/latest)'
                }
                Write-Host 'Pages: build FALHOU -- disparando 1 rebuild (caso da onda 41 era transitorio)...' -ForegroundColor Yellow
                & gh api -X POST $repoApi | Out-Null
                $tentouRebuild = $true
            }
        }
        Write-Host 'CONFIRME AO VIVO antes de dizer NO AR:' -ForegroundColor Green
        Write-Host '  https://mirow-co.github.io/mirow-site/pt/' -ForegroundColor Green
    }
    finally {
        Remove-Item Env:\GIT_INDEX_FILE -ErrorAction SilentlyContinue
        Remove-Item $indice -ErrorAction SilentlyContinue
    }
}
finally {
    Pop-Location
}
