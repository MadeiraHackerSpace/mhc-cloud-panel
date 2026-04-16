# setup-proxmox-portforward.ps1
# Cria port forward do Windows para o Proxmox no WSL Debian
# Execute como Administrador: powershell -ExecutionPolicy Bypass -File scripts\setup-proxmox-portforward.ps1

param(
    [string]$WslIp = "172.30.170.157",
    [int]$ProxmoxPort = 8006
)

# Verificar se é admin
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERRO: Execute este script como Administrador!" -ForegroundColor Red
    Write-Host "Clique direito no PowerShell -> Executar como administrador" -ForegroundColor Yellow
    exit 1
}

Write-Host "Configurando port forward: 0.0.0.0:$ProxmoxPort -> $WslIp`:$ProxmoxPort" -ForegroundColor Green

# Remover regra existente se houver
netsh interface portproxy delete v4tov4 listenport=$ProxmoxPort listenaddress=0.0.0.0 2>$null

# Criar novo port forward
netsh interface portproxy add v4tov4 listenport=$ProxmoxPort listenaddress=0.0.0.0 connectport=$ProxmoxPort connectaddress=$WslIp

# Verificar
Write-Host "`nPort forwards ativos:" -ForegroundColor Cyan
netsh interface portproxy show all

Write-Host "`nTestando acesso ao Proxmox via 127.0.0.1:$ProxmoxPort ..." -ForegroundColor Cyan
try {
    $result = Invoke-WebRequest -Uri "https://127.0.0.1:$ProxmoxPort/api2/json/version" -SkipCertificateCheck -TimeoutSec 5 -ErrorAction Stop
    Write-Host "Proxmox API acessivel!" -ForegroundColor Green
    Write-Host $result.Content
} catch {
    Write-Host "Aviso: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "O Proxmox pode estar iniciando. Aguarde alguns segundos e teste novamente." -ForegroundColor Yellow
}

Write-Host "`nConfiguracao concluida!" -ForegroundColor Green
Write-Host "Proxmox Web UI: https://127.0.0.1:$ProxmoxPort" -ForegroundColor Cyan
