# setup-proxmox-portforward.ps1
# Cria port forward do Windows para o Proxmox no WSL Debian.
# O IP do WSL muda a cada boot, portanto execute este script após cada reinicialização.
#
# Execute como Administrador:
#   powershell -ExecutionPolicy Bypass -File scripts\setup-proxmox-portforward.ps1
#
# Ou especifique o IP manualmente:
#   powershell -ExecutionPolicy Bypass -File scripts\setup-proxmox-portforward.ps1 -WslIp 172.30.170.157

param(
    [string]$WslIp = "",
    [int]$ProxmoxPort = 8006,
    [string]$WslDistro = "Debian"
)

# Verificar se é admin
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERRO: Execute este script como Administrador!" -ForegroundColor Red
    Write-Host "Clique direito no PowerShell -> Executar como administrador" -ForegroundColor Yellow
    exit 1
}

# Detectar IP do WSL automaticamente se não fornecido
if (-not $WslIp) {
    Write-Host "Detectando IP do WSL ($WslDistro)..." -ForegroundColor Cyan
    $WslIp = wsl -d $WslDistro -- bash -c "ip addr show eth0 | awk '/inet / {print \$2}' | cut -d/ -f1" 2>$null
    if (-not $WslIp) {
        Write-Host "ERRO: Nao foi possivel detectar o IP do WSL. Forneça -WslIp manualmente." -ForegroundColor Red
        exit 1
    }
    Write-Host "IP detectado: $WslIp" -ForegroundColor Green
}

Write-Host "Configurando port forward: 0.0.0.0:$ProxmoxPort -> ${WslIp}:$ProxmoxPort" -ForegroundColor Green

# Remover regra existente para essa porta
netsh interface portproxy delete v4tov4 listenport=$ProxmoxPort listenaddress=0.0.0.0 2>$null

# Criar novo port forward
netsh interface portproxy add v4tov4 listenport=$ProxmoxPort listenaddress=0.0.0.0 connectport=$ProxmoxPort connectaddress=$WslIp

# Listar regras ativas
Write-Host "`nPort forwards ativos:" -ForegroundColor Cyan
netsh interface portproxy show all

# Testar
Write-Host "`nTestando acesso em https://127.0.0.1:$ProxmoxPort ..." -ForegroundColor Cyan
Start-Sleep -Seconds 1
try {
    $resp = Invoke-WebRequest -Uri "https://127.0.0.1:${ProxmoxPort}/api2/json/version" -SkipCertificateCheck -TimeoutSec 8 -ErrorAction Stop
    Write-Host "Proxmox API acessivel! (HTTP $($resp.StatusCode))" -ForegroundColor Green
} catch [System.Net.WebException] {
    # HTTP 401 = Proxmox respondeu, apenas pede autenticacao
    if ($_.Exception.Response -and $_.Exception.Response.StatusCode -eq 401) {
        Write-Host "Proxmox API acessivel! (HTTP 401 - autenticacao necessaria, OK)" -ForegroundColor Green
    } else {
        Write-Host "Aviso: $($_.Exception.Message)" -ForegroundColor Yellow
        Write-Host "Verifique se o pveproxy esta rodando no WSL: wsl -d $WslDistro -- systemctl is-active pveproxy" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Aviso: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host "`nConfiguracao concluida!" -ForegroundColor Green
Write-Host "Proxmox Web UI : https://127.0.0.1:$ProxmoxPort" -ForegroundColor Cyan
Write-Host "PROXMOX_HOST   : https://host.docker.internal:$ProxmoxPort  (para o .env)" -ForegroundColor Cyan
