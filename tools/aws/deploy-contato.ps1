# deploy-contato.ps1 -- cria a rota de contato na API que a Mirow ja tem.
#
# Issue mirow-marketing#226. Idempotente: rodar de novo atualiza em vez de duplicar.
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File tools/aws/deploy-contato.ps1
#
# ASCII puro de proposito: o PS 5.1 le arquivo sem BOM como ANSI, e um travessao
# UTF-8 vira aspa curva que FECHA a string (ver a nota no CLAUDE.md).
#
# Pre-requisito que este script NAO faz e ninguem deve pular:
#   O SES precisa da identidade de ENVIO verificada, com os 3 CNAME de DKIM no DNS
#   (HostGator). Sem isso o e-mail sai sem assinatura, fora do SPF do dominio, e o
#   Microsoft 365 do proprio destinatario tende a jogar em lixo eletronico. Um
#   formulario cujo e-mail cai no spam esta tao quebrado quanto o que responde 404.
#
#   POR QUE SUBDOMINIO (envio.mirow.com.br) E NAO O DOMINIO PRINCIPAL
#   Pergunta do Mario (17/08): "nao perco governanca com isso?". Verificar o apex
#   daria a AWS autoridade para enviar como qualquer @mirow.com.br e obrigaria a
#   editar o SPF do dominio principal -- o registro que hoje governa o e-mail
#   humano no Microsoft 365. Com subdominio:
#     - o SPF de mirow.com.br NAO e tocado; o M365 segue autoridade unica dele;
#     - a AWS so pode assinar por envio.mirow.com.br, um espaco separado e obvio
#       de "e-mail de maquina";
#     - se um dia isso sair do ar, apaga-se o subdominio e nada mais e afetado.
#   O IAM deste script ainda estreita mais: ses:SendEmail so com FromAddress igual
#   ao remetente declarado -- um endereco, nao o subdominio inteiro.
#
#   Rode primeiro:
#     aws sesv2 create-email-identity --email-identity envio.mirow.com.br
#   e leve os 3 tokens para o DNS.

$ErrorActionPreference = 'Stop'

$Regiao      = 'sa-east-1'
$ApiId       = 'hp813geae7'
$Funcao      = 'mirow-contato-mailer'
$Role        = 'mirow-contato-mailer-role'
$Conta       = (aws sts get-caller-identity --query Account --output text)
$Destino     = 'andreas.mirow@mirow.com.br,felipe.diniz@mirow.com.br'
$Remetente   = 'site@envio.mirow.com.br'   # SUBDOMINIO: ver nota abaixo
$Origens     = 'https://mirow.com.br,https://www.mirow.com.br'

Write-Host "== 1/6 papel de execucao =="
$trust = '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}'
try { aws iam get-role --role-name $Role | Out-Null }
catch {
  aws iam create-role --role-name $Role --assume-role-policy-document $trust | Out-Null
  aws iam attach-role-policy --role-name $Role `
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole | Out-Null
  Start-Sleep -Seconds 10   # IAM demora a propagar; sem isso o create-function falha
}

# Permissao minima: enviar e-mail, e so a partir do remetente declarado.
$politica = '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":["ses:SendEmail"],"Resource":"*","Condition":{"StringEquals":{"ses:FromAddress":"' + $Remetente + '"}}}]}'
aws iam put-role-policy --role-name $Role --policy-name enviar-email --policy-document $politica | Out-Null

Write-Host "== 2/6 pacote =="
$zip = Join-Path $env:TEMP 'contato_mailer.zip'
if (Test-Path $zip) { Remove-Item $zip -Force }
Compress-Archive -Path 'tools/aws/contato_mailer.py' -DestinationPath $zip

Write-Host "== 3/6 funcao =="
$env_vars = "Variables={DESTINATARIOS=$Destino,REMETENTE=$Remetente,ALLOW_ORIGINS=$Origens}"
try {
  aws lambda get-function --function-name $Funcao --region $Regiao | Out-Null
  aws lambda update-function-code --function-name $Funcao --zip-file "fileb://$zip" --region $Regiao | Out-Null
  aws lambda wait function-updated --function-name $Funcao --region $Regiao
  aws lambda update-function-configuration --function-name $Funcao `
    --environment $env_vars --region $Regiao | Out-Null
} catch {
  aws lambda create-function --function-name $Funcao --runtime python3.12 `
    --role "arn:aws:iam::${Conta}:role/$Role" --handler contato_mailer.handler `
    --zip-file "fileb://$zip" --timeout 10 --memory-size 256 `
    --environment $env_vars --region $Regiao | Out-Null
}

Write-Host "== 4/6 integracao =="
$arn = "arn:aws:lambda:${Regiao}:${Conta}:function:$Funcao"
$intId = (aws apigatewayv2 get-integrations --api-id $ApiId --region $Regiao `
  --query "Items[?IntegrationUri=='$arn'].IntegrationId | [0]" --output text)
if ($intId -eq 'None' -or [string]::IsNullOrWhiteSpace($intId)) {
  $intId = (aws apigatewayv2 create-integration --api-id $ApiId --region $Regiao `
    --integration-type AWS_PROXY --integration-uri $arn `
    --payload-format-version 2.0 --query IntegrationId --output text)
}

Write-Host "== 5/6 rotas =="
# POST para enviar, OPTIONS para o preflight do navegador.
foreach ($rota in @('POST /contato', 'OPTIONS /contato')) {
  $existe = (aws apigatewayv2 get-routes --api-id $ApiId --region $Regiao `
    --query "Items[?RouteKey=='$rota'].RouteId | [0]" --output text)
  if ($existe -eq 'None' -or [string]::IsNullOrWhiteSpace($existe)) {
    aws apigatewayv2 create-route --api-id $ApiId --region $Regiao `
      --route-key $rota --target "integrations/$intId" | Out-Null
  } else {
    aws apigatewayv2 update-route --api-id $ApiId --region $Regiao `
      --route-id $existe --target "integrations/$intId" | Out-Null
  }
}

Write-Host "== 6/6 permissao para a API invocar =="
try {
  aws lambda add-permission --function-name $Funcao --statement-id apigw-contato `
    --action lambda:InvokeFunction --principal apigateway.amazonaws.com `
    --source-arn "arn:aws:execute-api:${Regiao}:${Conta}:$ApiId/*/*/contato" `
    --region $Regiao | Out-Null
} catch { Write-Host "   (permissao ja existia)" }

Write-Host ""
Write-Host "pronto. endpoint: https://$ApiId.execute-api.$Regiao.amazonaws.com/contato"
Write-Host "TESTE ANTES DE LIGAR NO SITE -- e nao confie no exit code, confira a caixa:"
Write-Host "  curl -X POST https://$ApiId.execute-api.$Regiao.amazonaws.com/contato ``"
Write-Host "    -H 'content-type: application/json' ``"
Write-Host "    -d '{\"nome\":\"Teste\",\"email\":\"voce@mirow.com.br\",\"mensagem\":\"teste\"}'"
