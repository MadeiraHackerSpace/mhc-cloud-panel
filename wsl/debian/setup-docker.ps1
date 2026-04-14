$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$distro = "Debian"

function Convert-ToWslPath([string]$windowsPath) {
  $p = $windowsPath -replace "\\", "/"
  if ($p -match "^([A-Za-z]):/(.*)$") {
    $drive = $Matches[1].ToLower()
    $rest = $Matches[2]
    return "/mnt/$drive/$rest"
  }
  throw "Caminho inválido para conversão WSL: $windowsPath"
}

$wslRepoRoot = Convert-ToWslPath $repoRoot

$distros = & wsl -l -q | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" }
if (-not ($distros -contains $distro)) {
  Write-Host "A distro '$distro' não está instalada no WSL. Instale com:"
  Write-Host "  wsl --install -d $distro"
  exit 1
}

& wsl -d $distro -- bash -lc "set -e; sudo apt update; sudo apt -y install ca-certificates curl gnupg"
& wsl -d $distro -- bash -lc "set -e; sudo install -m 0755 -d /etc/wsl.conf.d || true"
& wsl -d $distro -- bash -lc "set -e; sudo install -m 0644 '$wslRepoRoot/wsl/debian/wsl.conf' /etc/wsl.conf"

Write-Host "Se o systemd ainda não estiver ativo no WSL, execute no PowerShell:"
Write-Host "  wsl --shutdown"
Write-Host "E abra o Debian novamente antes de continuar."

& wsl -d $distro -- bash -lc "set -e; sudo bash '$wslRepoRoot/wsl/debian/install-docker.sh'"
& wsl -d $distro -- bash -lc "set -e; sudo bash '$wslRepoRoot/wsl/debian/apply-docker-config.sh'"

Write-Host "Docker instalado. Reabra o terminal do Debian para aplicar o grupo 'docker' (sem sudo)."
