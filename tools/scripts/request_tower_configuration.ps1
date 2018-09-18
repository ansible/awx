# Define parameters
[cmdletbinding()]
Param(
    [Alias("k")]
    [switch] $insecure = $false,

    [Alias("h")]
    [switch] $help,

    [Alias("s")]
    [string] $tower_url,

    [Alias("c")]
    [string] $host_config_key,

    [Alias("t")]
    [string] $job_template_id,

    [Alias("e")]
    [string] $extra_vars
)

# Initialize variables
Set-StrictMode -Version 2
$ErrorActionPreference = "Stop"
$retry_attempts = 10
$attempt = 0
$usage = @"
Request server configuration from Ansible Tower

Usage:
    Execution using positional parameters:
    $($MyInvocation.MyCommand.Name) https://example.towerhost.net 44d7507f2ead49af5fca80aa18fd24bc 38

    Ignore self-signed certificates using named parameters:
    $($MyInvocation.MyCommand.Name) -k -s https://example.towerhost.local -c 44d7507f2ead49af5fca80aa18fd24bc -t 38

    Execution using optional extra_vars:
    $($MyInvocation.MyCommand.Name) https://example.towerhost.net 44d7507f2ead49af5fca80aa18fd24bc 38 '{ key: value, dict: { key: value }}'

Options:
    -help, -h                                Show this message
    -tower_url, -s                           Tower server (e.g. https://<server address>[:server port]) (required)
    -insecure, -k                            Allow insecure SSL connections and transfers
    -host_config_key, -c <host config key>   Host config key (required)
    -job_template_id, -t <job template id>   Job template ID (required)
    -extra_vars, -e [<extra vars>]           Extra variables
"@

# Validate required arguments
If (-not $tower_url -or -not $host_config_key -or -not $job_template_id -or $help) {
    Write-Host $usage
    Exit 1
}

# Create Invoke-WebRequest JSON data hash tables
If (-not $extra_vars) {
    $data = @{
        host_config_key=$host_config_key
    }
} Else {
    $data = @{
        host_config_key=$host_config_key
        extra_vars=$extra_vars
    }
}

# Success on any 2xx status received, failure on only 404 status received, retry any other status every min for up to 10 min
While ($attempt -lt $retry_attempts) {
    Try {
        If ($insecure) {
            [System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true}
        }
        $resp = Invoke-WebRequest -ContentType application/json -Method POST -Body (ConvertTo-Json $data) -Uri $tower_url/api/v2/job_templates/$job_template_id/callback/
        If ($resp.StatusCode -match '^2[0-9]+$') {
            Exit 0
        }
    }
    Catch [System.Security.Authentication.AuthenticationException] {
        Write-Host $_
        Exit 1
    }
    Catch {
        $ex = $_
        $attempt++
        If ($([int]$ex.Exception.Response.StatusCode) -eq 404) {
            Write-Host "$([int]$ex.Exception.Response.StatusCode) received... encountered problem, halting"
            Exit 1
        }
        Write-Host "$([int]$ex.Exception.Response.StatusCode) received... retrying in 1 minute (Attempt $attempt)"
    }
    Finally {
        If ($insecure) {
            $sp = [System.Net.ServicePointManager]::FindServicePoint($tower_url)
            $sp.CloseConnectionGroup("") > $null
            [System.Net.ServicePointManager]::ServerCertificateValidationCallback = $null
        }
    }
    Start-Sleep -Seconds 60
}
Exit 1
