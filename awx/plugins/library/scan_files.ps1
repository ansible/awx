#!powershell
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# WANT_JSON
# POWERSHELL_COMMON

$params = Parse-Args $args $true;

$paths = Get-Attr $params "paths" $FALSE;
If ($paths -eq $FALSE)
{   
    Fail-Json (New-Object psobject) "missing required argument: paths";
}

$get_checksum = Get-Attr $params "get_checksum" $false | ConvertTo-Bool;
$recursive = Get-Attr $params "recursive" $false | ConvertTo-Bool;

function Date_To_Timestamp($start_date, $end_date)
{
    If($start_date -and $end_date)
    {
        Write-Output (New-TimeSpan -Start $start_date -End $end_date).TotalSeconds
    }
}

$files = @()

ForEach ($path In $paths)
{
    "Path: " + $path
    ForEach ($file in Get-ChildItem $path -Recurse: $recursive)
    {
        "File: " + $file.FullName
        $fileinfo = New-Object psobject
        Set-Attr $fileinfo "path" $file.FullName
        $info = Get-Item $file.FullName;
        $iscontainer = Get-Attr $info "PSIsContainer" $null;
        $length = Get-Attr $info "Length" $null;
        $extension = Get-Attr $info "Extension" $null;
        $attributes = Get-Attr $info "Attributes" "";
        If ($info)
        {
            $accesscontrol = $info.GetAccessControl();
        }
        Else
        {
            $accesscontrol = $null;
        }
        $owner = Get-Attr $accesscontrol "Owner" $null;
        $creationtime = Get-Attr $info "CreationTime" $null;
        $lastaccesstime = Get-Attr $info "LastAccessTime" $null;
        $lastwritetime = Get-Attr $info "LastWriteTime" $null;

        $epoch_date = Get-Date -Date "01/01/1970"
        If ($iscontainer)
        {
            Set-Attr $fileinfo "isdir" $TRUE;
        }
        Else
        {
            Set-Attr $fileinfo "isdir" $FALSE;
            Set-Attr $fileinfo "size" $length;
        }
        Set-Attr $fileinfo "extension" $extension;
        Set-Attr $fileinfo "attributes" $attributes.ToString();
        # Set-Attr $fileinfo "owner" $getaccesscontrol.Owner;
        # Set-Attr $fileinfo "owner" $info.GetAccessControl().Owner;
        Set-Attr $fileinfo "owner" $owner;
        Set-Attr $fileinfo "creationtime" (Date_To_Timestamp $epoch_date $creationtime);
        Set-Attr $fileinfo "lastaccesstime" (Date_To_Timestamp $epoch_date $lastaccesstime);
        Set-Attr $fileinfo "lastwritetime" (Date_To_Timestamp $epoch_date $lastwritetime);

        If (($get_checksum) -and -not $fileinfo.isdir)
        {
            $hash = Get-FileChecksum($file.FullName);
            Set-Attr $fileinfo "checksum" $hash;
        }

        $files += $fileinfo
    }
}

$result = New-Object psobject @{
    ansible_facts = New-Object psobject @{
        files = $files
    }
}

Exit-Json $result;
