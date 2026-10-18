#Requires -RunAsAdministrator
param(
    [Parameter(Mandatory = $true)][System.Net.IPAddress]$LanAddress,
    [ValidateRange(1024, 65535)][int]$Port = 8001,
    [switch]$Remove,
    [string]$ResultFile
)

$ErrorActionPreference = 'Stop'
$ruleName = 'MaisonElanLanPreview'
$description = 'Temporary MAISON ELAN LAN preview; local subnet only.'
$backendAddress = '127.0.0.1'
$completed = $false

try {
    foreach ($address in @($LanAddress)) {
        if ($address.AddressFamily -ne [System.Net.Sockets.AddressFamily]::InterNetwork) {
            throw 'Use explicit private IPv4 addresses.'
        }
        $octets = $address.GetAddressBytes()
        $private = $octets[0] -eq 10 -or
            ($octets[0] -eq 172 -and $octets[1] -ge 16 -and $octets[1] -le 31) -or
            ($octets[0] -eq 192 -and $octets[1] -eq 168)
        if (-not $private) { throw 'Use explicit private IPv4 addresses.' }
    }
    $existingRule = Get-NetFirewallRule -Name $ruleName -ErrorAction SilentlyContinue
    if ($existingRule -and $existingRule.Description -ne $description) {
        throw 'The firewall rule name is already in use; existing configuration preserved.'
    }
    $proxyKey = 'HKLM:\SYSTEM\CurrentControlSet\Services\PortProxy\v4tov4\tcp'
    $proxyName = "$LanAddress/$Port"
    $proxyProperties = Get-ItemProperty -Path $proxyKey -ErrorAction SilentlyContinue
    $existingTarget = if ($proxyProperties) { $proxyProperties.PSObject.Properties[$proxyName].Value }
    if ($existingTarget -and -not $existingRule) {
        throw 'This port already has a forwarding rule; existing configuration preserved.'
    }
    if ($Remove) {
        if ($existingRule) {
            if ($existingTarget) {
                & netsh.exe interface portproxy delete v4tov4 "listenaddress=$LanAddress" "listenport=$Port"
                if ($LASTEXITCODE -ne 0) { throw 'Unable to remove the preview forwarding rule.' }
            }
            Remove-NetFirewallRule -Name $ruleName
        }
        Write-Output 'MAISON ELAN LAN forwarding removed.'
    } else {
        $interface = Get-NetIPAddress -AddressFamily IPv4 -IPAddress $LanAddress.ToString()
        if (-not $interface) { throw 'The LAN address is not assigned to this Windows host.' }
        if (-not $existingTarget) {
            $listeners = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue |
                Where-Object { $_.LocalAddress -in @($LanAddress.ToString(), '0.0.0.0') }
            if ($listeners) { throw 'The selected Windows port is already in use.' }
        }
        # Use the verified Windows localhost relay rather than opening the Hyper-V VM firewall.
        & netsh.exe interface portproxy add v4tov4 "listenaddress=$LanAddress" "listenport=$Port" "connectaddress=$backendAddress" "connectport=$Port"
        if ($LASTEXITCODE -ne 0) { throw 'Unable to configure the preview forwarding rule.' }
        if ($existingRule) { Remove-NetFirewallRule -Name $ruleName }
        New-NetFirewallRule -Name $ruleName -DisplayName 'MAISON ELAN LAN Preview' `
            -Description $description -Direction Inbound -Action Allow -Protocol TCP `
            -LocalAddress $LanAddress.ToString() -LocalPort $Port -RemoteAddress LocalSubnet `
            -InterfaceAlias $interface.InterfaceAlias -Profile Any | Out-Null
        Write-Output "Android preview: http://${LanAddress}:$Port/"
    }
    $completed = $true
} catch {
    if ($ResultFile) { $_.Exception.Message | Set-Content -LiteralPath $ResultFile }
    throw
} finally {
    if ($completed -and $ResultFile) { 'ok' | Set-Content -LiteralPath $ResultFile }
}
