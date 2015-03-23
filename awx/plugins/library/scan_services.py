#!/usr/bin/env python

import re
from ansible.module_utils.basic import * # noqa

class BaseService(object):

    def __init__(self, module):
        self.module = module

class ServiceScanService(BaseService):

    def gather_services(self):
        services = {}
        service_path = self.module.get_bin_path("service")
        if service_path is None:
            return None
        initctl_path = self.module.get_bin_path("initctl")
        chkconfig_path = self.module.get_bin_path("chkconfig")
        # Upstart and sysvinit
        if initctl_path is not None and chkconfig_path is None:
            rc, stdout, stderr = self.module.run_command("%s --status-all 2>&1 | grep -E \"\\[ (\\+|\\-) \\]\"" % service_path, use_unsafe_shell=True)
            for line in stdout.split("\n"):
                line_data = line.split()
                if len(line_data) < 4:
                    continue # Skipping because we expected more data
                service_name = " ".join(line_data[3:])
                service_state = "running" if line_data[1] == "+" else "stopped"
                services[service_name] = {"name": service_name, "state": service_state, "source": "sysv"}
            rc, stdout, stderr = self.module.run_command("%s list" % initctl_path)
            real_stdout = stdout.replace("\r","")
            for line in real_stdout.split("\n"):
                line_data = line.split()
                if len(line_data) < 2:
                    continue
                service_name = line_data[0]
                if line_data[1].find("/") == -1: # we expect this to look like: start/running
                    continue
                service_goal = line_data[1].split("/")[0]
                service_state = line_data[1].split("/")[1].replace(",","")
                if len(line_data) > 3: # If there's a pid associated with the service it'll be on the end of this string "process 418"
                    if line_data[2] == 'process':
                        pid = line_data[3]
                    else:
                        pid = None
                else:
                    pid = None
                payload = {"name": service_name, "state": service_state, "goal": service_goal, "source": "upstart"}
                services[service_name] = payload

        # RH sysvinit
        elif chkconfig_path is not None:
            #print '%s --status-all | grep -E "is (running|stopped)"' % service_path
            rc, stdout, stderr = self.module.run_command('%s --status-all | grep -E "dead|is (running|stopped)"' % service_path, use_unsafe_shell=True)
            for line in stdout.split("\n"):
                line_data = line.split()
                if re.match(".+\(pid.+[0-9]+\).+is running", line) is not None and len(line_data) == 5:
                    service_name = line_data[0]
                    service_pid = line_data[2].replace(")","")
                    service_state = "running"
                elif len(line_data) > 2 and line_data[1] == "dead":
                    service_name = line_data[0]
                    service_pid = None
                    service_state = "dead"
                elif len(line_data) == 3:
                    service_name = line_data[0]
                    service_pid = None
                    service_state = "stopped"
                else:
                    continue
                service_data = {"name": service_name, "state": service_state, "source": "sysv"}
                services[service_name] = service_data
            # rc, stdout, stderr = self.module.run_command("%s --list" % chkconfig_path)
            # Do something with chkconfig status
        return services

class SystemctlScanService(BaseService):

    def systemd_enabled(self):
        # Check if init is the systemd command, using comm as cmdline could be symlink
        try:
            f = open('/proc/1/comm', 'r')
        except IOError:
            # If comm doesn't exist, old kernel, no systemd
            return False
        for line in f:
            if 'systemd' in line:
                return True
        return False

    def gather_services(self):
        services = {}
        if not self.systemd_enabled():
            return None
        systemctl_path = self.module.get_bin_path("systemctl", opt_dirs=["/usr/bin", "/usr/local/bin"])
        if systemctl_path is None:
            return None
        rc, stdout, stderr = self.module.run_command("%s list-unit-files --type=service | tail -n +2 | head -n -2" % systemctl_path, use_unsafe_shell=True)
        for line in stdout.split("\n"):
            line_data = line.split()
            if len(line_data) != 2:
                continue
            services[line_data[0]] = {"name": line_data[0],
                                      "state": "running" if line_data[1] == "enabled" else "stopped",
                                      "source": "systemd"}
        return services

def main():
    module = AnsibleModule(argument_spec = dict())
    service_modules = (ServiceScanService, SystemctlScanService)
    all_services = {}
    for svc_module in service_modules:
        svcmod = svc_module(module)
        svc = svcmod.gather_services()
        if svc is not None:
            all_services.update(svc)
    results = dict(ansible_facts=dict(services=all_services))
    module.exit_json(**results)

main()
