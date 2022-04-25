Create a RHEL box and then do the following.
```bash
sudo mkdir -p /usr/share/sosreport/sos/plugins
sudo yum install sos
cp controller.py /usr/share/sosreport/sos/plugins
sudo chmod 644 /usr/share/sosreport/sos/plugins/controller.py
ln -s /usr/share/sosreport/sos/plugins/controller.py `find `find /usr/lib -name sos` -name plugins`
sosreport -l | grep controller
```

The results should be:
```bash
# sosreport -l | grep controller
 controller           Ansible Automation Platform controller information
```

To run only the controller plugin run: `sosreport --only-plugins controller`

