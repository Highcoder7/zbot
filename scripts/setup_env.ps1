# Creates .env from local «апи ключи» for deploy (run once after clone)
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$keysFile = Join-Path $root "апи ключи"
$envFile = Join-Path $root ".env"

if (-not (Test-Path $keysFile)) {
    Write-Error "Файл «апи ключи» не найден. Скопируйте апи ключи.example и заполните ключи."
    exit 1
}

$map = @{}
Get-Content $keysFile -Encoding UTF8 | ForEach-Object {
    $line = $_.Trim()
    if (-not $line -or $line.StartsWith("#") -or $line -notmatch "=") { return }
    $k, $v = $line -split "=", 2
    $map[$k.Trim().ToLower()] = $v.Trim().Trim('"').Trim("'")
}

$tg = $map["tg api key"] ?? $map["tg bot token"]
$openai = $map["open ai api key"] ?? $map["openai api key"]
$openaiModel = $map["open ai model"] ?? "gpt-4o"
$contentModel = $map["open ai content model"] ?? "gpt-5.5"
$claude = $map["calude api key"] ?? $map["claude api key"]
$claudeModel = $map["claude model"] ?? "claude-sonnet-4-6"

if (-not $tg -or -not $openai) {
    Write-Error "В «апи ключи» должны быть tg api key и open ai api key."
    exit 1
}

@"
TG_BOT_TOKEN=$tg
OPENAI_API_KEY=$openai
OPENAI_MODEL=$openaiModel
OPENAI_CONTENT_MODEL=$contentModel
CLAUDE_API_KEY=$claude
CLAUDE_MODEL=$claudeModel
"@ | Set-Content $envFile -Encoding UTF8

Write-Host "Created .env in $root"
