### Upgrade Ansible version in AWX to latest Ansible devel
AWX 17 comes shipped with Ansible version 2.9.2*, but if you want to upgrade the Ansible version it can be some hassle. 
Here is how to upgrade the Ansible version for AWX :) 

<i> Note: the upgrade has to happen in the docker containers! </i>

Login and run bash commands on the web container:
```bash
$ docker exec -it awx_web bash
```
Add new mirrorlist so you can install epel-release:
```bash
$ sed -i 's/mirrorlist/#mirrorlist/g' /etc/yum.repos.d/CentOS-Linux-*
$ sed -i 's|#baseurl=http://mirror.centos.org|baseurl=http://vault.centos.org|g' /etc/yum.repos.d/CentOS-Linux-*
```
Update, install epel-release, upgrad pip:
```bash
$ dnf update -y
$ dnf install epel-release
$ pip install --upgrade pip
```
Create a new virtual environment for awx and install depend's. <i>(name the virtual environment what you want, in this example its named "ansible"</i>:
```bash
$ virtualenv /var/lib/awx/venv/ansible 
$ yum install -y gcc
$ yum install -y python-devel
```
Now we need to install some utils in the newly created virtual environment:
```bash
$ /var/lib/awx/venv/ansible/bin/pip install python-memcached psutil
```
Then install ansible in the new virtual environment:
```bash
$ /var/lib/awx/venv/ansible/bin/pip install -U ansible
```
<i>Note: If you want to install an version of ansible, change ansible with </i> `"ansible == 2.9.28"`

If you get an error that ansible is allready installed, uninstall it with: 
```bash
$ /var/lib/awx/venv/ansible/bin/pip uninstall -U "ansible == version"
```
Exit the container:
```bash
$ exit
```
Now do the same steps on the task container:
```bash
$ docker exec -it awx_task bash
```
etc.... 

Make awx use our new virtual environment: 
<i> Change the marked parts to fit your deployment </i>
```bash
$ curl  -u 'admin:password' -X PATCH -H 'Content-Type: application/json' http://awx-ip/api/v2/organizations/org-name/ -d '
```
or in the web gui: 
url: http://awx-ip/api/v2/organizations/
Find the line: `"custom_virtualenv":""` and add the new directory. Example: 
`"custom_virtualenv":"/var/lib/awx/venv/ansible/"`
