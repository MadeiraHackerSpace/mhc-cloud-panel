# install-docker.ps1 — instala Docker Desktop no Windows via winget ou download direto
# Execute como Administrador: powershell -ExecutionPolicy Bypass -File .\scripts\install-docker.ps1

#Requires -RunAsAdministrator

$ErrorActionPreference = "Stop"

function Write-Info  { param($msg) Write-Host "[INFO]  $msg" -ForegroundColor Green }
function Write-Warn  { param($msg) Write-Host "[WARN]  $msg" -ForegroundColor Yellow }
function Write-Err   { param($msg) Write-Host "[ERROR] $msg" -ForegroundColor Red; exit 1 }

# ── Verifica se já está instalado ────────────────────────────────────────────
if (Get-Command docker -ErrorAction SilentlyContinue) {
    Write-Info "Docker já está instalado: $(docker --version)"
    try { Write-Info "Docker Compose: $(docker compose version)" } catch {}
    exit 0
}

Write-Info "Docker não encontrado. Iniciando instalação..."

# ── Tenta instalar via winget (Windows 10 1709+ / Windows 11) ────────────────
if (Get-Command winget -ErrorAction SilentlyContinue) {
    Write-Info "Instalando Docker Desktop via winget..."
    winget install --id Docker.DockerDesktop --accept-source-agreements --accept-package-agreements
    if ($LASTEXITCODE -eq 0) {
        Write-Info "Docker Desktop instalado com sucesso via winget."
        Write-Warn "Reinicie o sistema e abra o Docker Desktop para concluir a configuração."
        exit 0
    }
    Write-Warn "winget falhou (código $LASTEXITCODE). Tentando download direto..."
}

# ── Fallback: download direto do instalador ───────────────────────────────────
$installerUrl  = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
$installerPath = "$env:TEMP\DockerDesktopInstaller.exe"

Write-Info "Baixando Docker Desktop Installer..."
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath -UseBasicParsing

Write-Info "Executando instalador (modo silencioso)..."
Start-Process -FilePath $installerPath -ArgumentList "install --quiet --accept-license" -Wait

if (Get-Command docker -ErrorAction SilentlyContinue) {
    Write-Info "Docker Desktop instalado com sucesso!"
    Write-Warn "Reinicie o sistema e abra o Docker Desktop para concluir a configuração."
} else {
    Write-Warn "Instalação concluída, mas 'docker' ainda não está no PATH."
    Write-Warn "Reinicie o sistema e abra o Docker Desktop para finalizar."
}

Remove-Item $installerPath -Force -ErrorAction SilentlyContinue
