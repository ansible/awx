export default [
	{
		"details": {
			"detected_problem_log_perms": [{
				"log_perms_dirfilename": "/var/log/cron",
				"log_perms_sensitive": true,
				"log_perms_ls_line": "-rw-r--r--.  1 root root   15438 May 25 10:01 cron"
			}],
			"error_key": "HARDENING_LOGGING_3_LOG_PERMS"
		},
		"id": 709784525,
		"rule_id": "hardening_logging_log_perms|HARDENING_LOGGING_3_LOG_PERMS",
		"system_id": "f31b6265939d4a8492d3ce9655dc94be",
		"account_number": "540155",
		"uuid": "d195e3c5e5e6469781c4e59fa3f5ba87",
		"date": "2017-05-25T14:01:19.000Z",
		"rule": {
			"summary_html": "<p>Issues related to system logging and auditing were detected on your system. Important services are disabled or log file permissions are not secure.</p>\n",
			"generic_html": "<p>Issues related to system logging and auditing were detected on your system.</p>\n<p>Red Hat recommends that the logging service <code>rsyslog</code> and the auditing service <code>auditd</code> are enabled and that log files in <code>/var/log</code> have secure permissions.</p>\n",
			"more_info_html": "<ul>\n<li><a href=\"https://access.redhat.com/solutions/1491573\">Why is <code>/var/log/cron</code> world readable in RHEL7?</a></li>\n<li><a href=\"https://access.redhat.com/documentation/en-US/Red_Hat_Enterprise_Linux/6/html/Deployment_Guide/s2-services-chkconfig.html\">Using the chkconfig Utility</a> to configure services on RHEL 6</li>\n<li><a href=\"https://access.redhat.com/documentation/en-US/Red_Hat_Enterprise_Linux/7/html/System_Administrators_Guide/sect-Managing_Services_with_systemd-Services.html\">Managing System Services</a> to configure services on RHEL 7</li>\n<li>The Customer Portal page for the <a href=\"https://access.redhat.com/security/\">Red Hat Security Team</a> contains more information about policies, procedures, and alerts for Red Hat products.</li>\n<li>The Security Team also maintains a frequently updated blog at <a href=\"https://securityblog.redhat.com\">securityblog.redhat.com</a>.</li>\n</ul>\n",
			"severity": "INFO",
			"ansible": false,
			"ansible_fix": false,
			"ansible_mitigation": false,
			"rule_id": "hardening_logging_log_perms|HARDENING_LOGGING_3_LOG_PERMS",
			"error_key": "HARDENING_LOGGING_3_LOG_PERMS",
			"plugin": "hardening_logging_log_perms",
			"description": "Decreased security in system logging permissions",
			"summary": "Issues related to system logging and auditing were detected on your system. Important services are disabled or log file permissions are not secure.\n",
			"generic": "Issues related to system logging and auditing were detected on your system.\n\nRed Hat recommends that the logging service `rsyslog` and the auditing service `auditd` are enabled and that log files in `/var/log` have secure permissions.\n",
			"reason": "<p>Log files have permission issues.</p>\n<p>The following files or directories in <code>/var/log</code> have file permissions that differ from the default RHEL configuration and are possibly non-secure. Red Hat recommends that the file permissions be adjusted to more secure settings.</p>\n<table border=\"1\" align=\"left\">\n  <tr>\n    <th style=\"text-align:center;\">File or directory name</th>\n    <th style=\"text-align:center;\">Detected problem</th>\n    <th style=\"text-align:center;\">Output from <code>ls -l</code></th>\n  </tr>\n\n<tr>\n\n<td><code>/var/log/cron</code></td><td>Users other than <code>root</code> can read or write.</td><td><code>-rw-r--r--.  1 root root   15438 May 25 10:01 cron</code></td>\n\n</td>\n\n</table>\n\n\n\n",
			"type": null,
			"more_info": "* [Why is `/var/log/cron` world readable in RHEL7?](https://access.redhat.com/solutions/1491573)\n* [Using the chkconfig Utility](https://access.redhat.com/documentation/en-US/Red_Hat_Enterprise_Linux/6/html/Deployment_Guide/s2-services-chkconfig.html) to configure services on RHEL 6\n* [Managing System Services](https://access.redhat.com/documentation/en-US/Red_Hat_Enterprise_Linux/7/html/System_Administrators_Guide/sect-Managing_Services_with_systemd-Services.html) to configure services on RHEL 7\n* The Customer Portal page for the [Red Hat Security Team](https://access.redhat.com/security/) contains more information about policies, procedures, and alerts for Red Hat products.\n* The Security Team also maintains a frequently updated blog at [securityblog.redhat.com](https://securityblog.redhat.com).\n",
			"active": true,
			"node_id": null,
			"category": "Security",
			"retired": false,
			"reboot_required": false,
			"publish_date": "2017-05-16T04:08:34.000Z",
			"rec_impact": 1,
			"rec_likelihood": 1,
			"resolution": "<p>Red Hat recommends that you perform the following adjustments:</p>\n<p>Fixing permission issues depends on whether there is a designated safe group on your system that has Read access to the log files. This situation might exist if you want to allow certain administrators to see the log files without becoming <code>root</code>. To prevent log tampering, no other user than <code>root</code> should have permissions to Write to the log files. (The <code>btmp</code> and <code>wtmp</code> files are owned by the <code>utmp</code> group but other users should still be unable to write to them.)</p>\n<p><strong>Fix for a default RHEL configuration</strong></p>\n<p>(No designated group for reading log files)</p>\n<pre><code>chown root:root /var/log/cron\nchmod u=rw,g-x,o-rwx /var/log/cron\n</code></pre><p><strong>Fix for a configuration with a designated safe group for reading log files</strong></p>\n<p>In the following lines, substitute the name of your designated safe group for the string <code>safegroup</code>:</p>\n<pre><code>chown root:safegroup /var/log/cron\nchmod u=rw,g-x,o-rwx /var/log/cron\n</code></pre>"
		},
		"maintenance_actions": []
	}, {
		"details": {
			"error_key": "TZDATA_NEED_UPGRADE_INFO_NEED_MANUAL_ACTION"
		},
		"id": 709784565,
		"rule_id": "tzdata_need_upgrade|TZDATA_NEED_UPGRADE_INFO_NEED_MANUAL_ACTION",
		"system_id": "f31b6265939d4a8492d3ce9655dc94be",
		"account_number": "540155",
		"uuid": "d195e3c5e5e6469781c4e59fa3f5ba87",
		"date": "2017-05-25T14:01:19.000Z",
		"rule": {
			"summary_html": "<p>System clock inaccurate when a leap second event happens in a non-NTP system without following the TAI timescale.</p>\n",
			"generic_html": "<p>System clock inaccurate when a leap second event happens in a non-NTP system without following the TAI timescale.</p>\n",
			"more_info_html": "",
			"severity": "INFO",
			"ansible": false,
			"ansible_fix": false,
			"ansible_mitigation": false,
			"rule_id": "tzdata_need_upgrade|TZDATA_NEED_UPGRADE_INFO_NEED_MANUAL_ACTION",
			"error_key": "TZDATA_NEED_UPGRADE_INFO_NEED_MANUAL_ACTION",
			"plugin": "tzdata_need_upgrade",
			"description": "System clock inaccurate when a leap second event happens in a non-NTP system without following the TAI timescale",
			"summary": "System clock inaccurate when a leap second event happens in a non-NTP system without following the TAI timescale.\n",
			"generic": "System clock inaccurate when a leap second event happens in a non-NTP system without following the TAI timescale.\n",
			"reason": "<p>This system running as a non-NTP system is following the <strong>UTC timescale</strong>. In this situation, manual correction is required to avoid system clock inaccuracy when a leap second event happens.</p>\n",
			"type": null,
			"more_info": null,
			"active": true,
			"node_id": "1465713",
			"category": "Stability",
			"retired": false,
			"reboot_required": false,
			"publish_date": null,
			"rec_impact": 2,
			"rec_likelihood": 1,
			"resolution": "<p>The system clock of this system needs manual correction when a leap second event happens. For example:</p>\n<pre>\n<code>\n# date -s \"20170101 HH:MM:SS\"\n</code>\n</pre>\n\n<p>You need to replace &quot;HH:MM:SS&quot; with the accurate time after the leap second occurs.</p>\n"
		},
		"maintenance_actions": []
	}
]
