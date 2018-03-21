Param(
    [string]$tower_url,
    [string]$host_config_key,
    [string]$job_template_id,
    [string]$extra_vars
)

Set-StrictMode -Version 2
$ErrorActionPreference = "Stop"

If(-not $tower_url -or -not $host_config_key -or -not $job_template_id)
{
    Write-Host "Requests server configuration from Ansible Tower"
    Write-Host "Usage: $($MyInvocation.MyCommand.Name) https://<server address>[:server port] <host config key> <job template id>"
    Write-Host "Example: $($MyInvocation.MyCommand.Name) https://example.towerhost.net 44d7507f2ead49af5fca80aa18fd24bc 38"
    Write-Host "Example with extra_vars: $($MyInvocation.MyCommand.Name) https://example.towerhost.net 44d7507f2ead49af5fca80aa18fd24bc 38 '{ key: value, dict: { key: value }}'"
    Exit 1
}

$retry_attempts = 10
$attempt = 0

If(-not $extra_vars)
{
    $data = @{
        host_config_key=$host_config_key
    }
} Else {
    $data = @{
        host_config_key=$host_config_key
        extra_vars=$extra_vars
    }
}

While ($attempt -lt $retry_attempts) {
    Try {
        $resp = Invoke-WebRequest -ContentType application/json -Method POST -Body (ConvertTo-Json $data) -Uri $tower_url/api/v2/job_templates/$job_template_id/callback/

        If ($resp.StatusCode -match '^2[0-9]+$') {
            Exit 0
        } ElseIf ($resp.StatusCode -eq 404) {
            Write-Host "$resp.StatusCode received... encountered problem, halting"
            Exit 1
        }
    }
    Catch {
        $ex = $_
        $attempt++
        Write-Host "$([int]$ex.Exception.Response.StatusCode) received... retrying in 1 minute (Attempt $attempt)"
    }
    Start-Sleep -Seconds 60
}
Exit 1
