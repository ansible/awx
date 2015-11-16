Param(
    [string]$tower_url,
    [string]$host_config_key,
    [string]$job_template_id
)

Set-StrictMode -Version 2
$ErrorActionPreference = "Stop"

If(-not $tower_url -or -not $host_config_key -or -not $job_template_id)
{
    Write-Host "Requests server configuration from Ansible Tower"
    Write-Host "Usage: $($MyInvocation.MyCommand.Name) <server address>[:server port] <host config key> <job template id>"
    Write-Host "Example: $($MyInvocation.MyCommand.Name) example.towerhost.net 44d7507f2ead49af5fca80aa18fd24bc 38"
    Exit 1
}

$retry_attempts = 10
$attempt = 0

$data = @{
    host_config_key=$host_config_key
}

While ($attempt -lt $retry_attempts) {
    Try {
        $resp = Invoke-WebRequest -Method POST -Body $data -Uri http://$tower_url/api/v1/job_templates/$job_template_id/callback/ -UseBasicParsing

        If($resp.StatusCode -eq 202) {
            Exit 0
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