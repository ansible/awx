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

$uninstall_native_path = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
$uninstall_wow6432_path = "HKLM:\SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall"

if ([System.IntPtr]::Size -eq 4) {

    # This is a 32-bit Windows system, so we only check for 32-bit programs, which will be
    # at the native registry location.

    [PSObject []]$packages = Get-ChildItem -Path $uninstall_native_path |
        Get-ItemProperty |
        Select-Object -Property @{Name="name"; Expression={$_."DisplayName"}},
            @{Name="version"; Expression={$_."DisplayVersion"}},
            @{Name="publisher"; Expression={$_."Publisher"}},
            @{Name="arch"; Expression={ "Win32" }} |
        Where-Object { $_.name }

} else {

    # This is a 64-bit Windows system, so we check for 64-bit programs in the native
    # registry location, and also for 32-bit programs under Wow6432Node.

    [PSObject []]$packages = Get-ChildItem -Path $uninstall_native_path |
        Get-ItemProperty |
        Select-Object -Property @{Name="name"; Expression={$_."DisplayName"}},
            @{Name="version"; Expression={$_."DisplayVersion"}},
            @{Name="publisher"; Expression={$_."Publisher"}},
            @{Name="arch"; Expression={ "Win64" }} |
        Where-Object { $_.name }

    $packages += Get-ChildItem -Path $uninstall_wow6432_path |
        Get-ItemProperty |
        Select-Object -Property @{Name="name"; Expression={$_."DisplayName"}},
            @{Name="version"; Expression={$_."DisplayVersion"}},
            @{Name="publisher"; Expression={$_."Publisher"}},
            @{Name="arch"; Expression={ "Win32" }} |
        Where-Object { $_.name }

}

$result = New-Object psobject @{
    ansible_facts = New-Object psobject @{
        packages = $packages
    }
    changed = $false
}

Exit-Json $result;
