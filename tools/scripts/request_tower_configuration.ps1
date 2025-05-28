#!/usr/bin/env pwsh

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
$retry_attempts = 10
$attempt = 0
$usage = @"
Request server configuration from Ansible Tower

Usage:
    Execution using positional parameters:
    $($MyInvocation.MyCommand.Name) https://example.platformhost.net 44d7507f2ead49af5fca80aa18fd24bc 38

    Ignore self-signed certificates using named parameters:
    $($MyInvocation.MyCommand.Name) -k -s https://example.platformhost.local -c 44d7507f2ead49af5fca80aa18fd24bc -t 38

    Execution using optional extra_vars:
    $($MyInvocation.MyCommand.Name) https://example.platformhost.net 44d7507f2ead49af5fca80aa18fd24bc 38 '{ key: value, dict: { key: value }}'

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
$data = @{
    host_config_key = $host_config_key
}
If ($extra_vars) {
    $data.extra_vars = $extra_vars
}

# Ensure TLS 1.2 is enabled (this isn't on by default on older .NET versions)
[Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12

$invoke_params = @{
    ContentType = 'application/json'
    Method = 'POST'
    Body = (ConvertTo-Json $data)
    Uri = "$tower_url/api/v2/job_templates/$job_template_id/callback/"
    UseBasicParsing = $true
    ErrorAction = 'Stop'
}

$invoke_command = Get-Command -Name Invoke-WebRequest
$legacy_insecure = $insecure
If ('SkipCertificateCheck' -in $invoke_command.Parameters.Keys) {
    $invoke_params.SkipCertificateCheck = $insecure
    $legacy_insecure = $false
}
Else {
    Add-Type -TypeDefinition @'
using System.Net;
using System.Security.Cryptography.X509Certificates;

public class TrustAllCertsPolicy : ICertificatePolicy {
    public bool CheckValidationResult(ServicePoint srvPoint, X509Certificate certificate,
            WebRequest request, int certificateProblem) {
        return true;
    }
}
'@
}
$old_validation_policy = [System.Net.ServicePointManager]::CertificatePolicy

# Success on any 2xx status received, failure on only 404 status received, retry any other status every min for up to 10 min
While ($attempt -lt $retry_attempts) {
    Try {
        If ($legacy_insecure) {
            [System.Net.ServicePointManager]::CertificatePolicy = New-Object -TypeName TrustAllCertsPolicy
        }
        $null = Invoke-WebRequest @invoke_params
        Exit 0
    }
    Catch {
        $exp = $_.Exception

        # The StatusCode is only present on certain exception which differ across PowerShell versions.
        $status_code = If ($exp.GetType().FullName -in @(
            'System.Net.WebException',  # Windows PowerShell (<=5.1)
            'Microsoft.PowerShell.Commands.HttpResponseException'  # PowerShell (6+)
        )) {
            $exp.Response.StatusCode
        }

        # WinPS cert validation errors are a WebException but have no StatusCode so we need to check that explicitly.
        If ($null -ne $status_code) {
            $attempt++
            
            $msg = "$([int]$status_code) ($status_code) received... "

            If ([int]$status_code -eq 404) {
                Write-Host "$msg encountered problem, halting"
                Exit 1
            }

            Write-Host "$msg retrying in 1 minute (Attempt $attempt)"
        }
        Else {
            Write-Host "Unknown error received... $($_.ToString()) ($($exp.GetType().FullName))"
            Exit 1
        }
    }
    Finally {
        If ($legacy_insecure) {
            $sp = [System.Net.ServicePointManager]::FindServicePoint($invoke_params.Uri)
            $sp.CloseConnectionGroup("") > $null
            [System.Net.ServicePointManager]::CertificatePolicy = $old_validation_policy
        }
    }
    Start-Sleep -Seconds 60
}
Exit 1
