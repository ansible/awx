export default [
    {
		"details": {
			"vulnerable_kernel": "3.10.0-123.el7",
			"package_name": "kernel",
			"error_key": "KERNEL_CVE_2016_5195"
		},
		"id": 709784485,
		"rule_id": "CVE_2016_5195_kernel|KERNEL_CVE_2016_5195",
		"system_id": "f31b6265939d4a8492d3ce9655dc94be",
		"account_number": "540155",
		"uuid": "d195e3c5e5e6469781c4e59fa3f5ba87",
		"date": "2017-05-25T14:01:19.000Z",
		"rule": {
			"summary_html": "<p>A flaw was found in the Linux kernel&#39;s memory subsystem. An unprivileged local user could use this flaw to write to files they would normally only have read-only access to and thus increase their privileges on the system.</p>\n",
			"generic_html": "<p>A race condition was found in the way Linux kernel&#39;s memory subsystem handled breakage of the read only shared mappings COW situation on write access. An unprivileged local user could use this flaw to write to files they should normally have read-only access to, and thus increase their privileges on the system.</p>\n<p>A process that is able to mmap a file is able to race Copy on Write (COW) page creation (within get_user_pages) with madvise(MADV_DONTNEED) kernel system calls. This would allow modified pages to bypass the page protection mechanism and modify the mapped file.  The vulnerability could be abused by allowing an attacker to modify existing setuid files with instructions to elevate permissions.  This attack has been found in the wild. </p>\n<p>Red Hat recommends that you update the kernel package or apply mitigations.</p>\n",
			"more_info_html": "<ul>\n<li>For more information about the flaw see <a href=\"https://access.redhat.com/security/cve/CVE-2016-5195\">CVE-2016-5195</a></li>\n<li>To learn how to upgrade packages, see &quot;<a href=\"https://access.redhat.com/solutions/9934\">What is yum and how do I use it?</a>&quot;</li>\n<li>The Customer Portal page for the <a href=\"https://access.redhat.com/security/\">Red Hat Security Team</a> contains more information about policies, procedures, and alerts for Red Hat Products.</li>\n<li>The Security Team also maintains a frequently updated blog at <a href=\"https://securityblog.redhat.com\">securityblog.redhat.com</a>.</li>\n</ul>\n",
			"severity": "WARN",
			"ansible": true,
			"ansible_fix": false,
			"ansible_mitigation": false,
			"rule_id": "CVE_2016_5195_kernel|KERNEL_CVE_2016_5195",
			"error_key": "KERNEL_CVE_2016_5195",
			"plugin": "CVE_2016_5195_kernel",
			"description": "Kernel vulnerable to privilege escalation via permission bypass (CVE-2016-5195)",
			"summary": "A flaw was found in the Linux kernel's memory subsystem. An unprivileged local user could use this flaw to write to files they would normally only have read-only access to and thus increase their privileges on the system.",
			"generic": "A race condition was found in the way Linux kernel's memory subsystem handled breakage of the read only shared mappings COW situation on write access. An unprivileged local user could use this flaw to write to files they should normally have read-only access to, and thus increase their privileges on the system.\n\nA process that is able to mmap a file is able to race Copy on Write (COW) page creation (within get_user_pages) with madvise(MADV_DONTNEED) kernel system calls. This would allow modified pages to bypass the page protection mechanism and modify the mapped file.  The vulnerability could be abused by allowing an attacker to modify existing setuid files with instructions to elevate permissions.  This attack has been found in the wild. \n\nRed Hat recommends that you update the kernel package or apply mitigations.",
			"reason": "<p>A flaw was found in the Linux kernel&#39;s memory subsystem. An unprivileged local user could use this flaw to write to files they would normally have read-only access to and thus increase their privileges on the system.</p>\n<p>This host is affected because it is running kernel <strong>3.10.0-123.el7</strong>. </p>\n<p>There is currently no mitigation applied and your system is vulnerable.</p>\n",
			"type": null,
			"more_info": "* For more information about the flaw see [CVE-2016-5195](https://access.redhat.com/security/cve/CVE-2016-5195)\n* To learn how to upgrade packages, see \"[What is yum and how do I use it?](https://access.redhat.com/solutions/9934)\"\n* The Customer Portal page for the [Red Hat Security Team](https://access.redhat.com/security/) contains more information about policies, procedures, and alerts for Red Hat Products.\n* The Security Team also maintains a frequently updated blog at [securityblog.redhat.com](https://securityblog.redhat.com).",
			"active": true,
			"node_id": "2706661",
			"category": "Security",
			"retired": false,
			"reboot_required": false,
			"publish_date": "2016-10-31T04:08:33.000Z",
			"rec_impact": 2,
			"rec_likelihood": 2,
			"resolution": "<p>Red Hat recommends that you update the <code>kernel</code> package and restart the system:</p>\n<pre><code># yum update kernel\n# reboot\n</code></pre><p><strong>or</strong></p>\n<p>Alternatively, this issue can be addressed by applying mitigations until the machine is restarted with the updated kernel package.</p>\n<p>Please refer to the Resolve Tab in <a href=\"https://access.redhat.com/security/vulnerabilities/2706661\">the vulnerability article</a> for information about the mitigation and the latest information.</p>\n"
		},
		"maintenance_actions": [{
			"done": false,
			"id": 29885,
			"maintenance_plan": {
				"maintenance_id": 12195,
				"name": null,
				"description": null,
				"start": null,
				"end": null,
				"created_by": "rhn-support-jnewton",
				"silenced": false,
				"hidden": true,
				"suggestion": "proposed",
				"remote_branch": null
			}
		}]
	},
    {
		"details": {
			"mitigation_conf": "no",
			"sysctl_live_ack_limit": "100",
			"package_name": "kernel",
			"sysctl_live_ack_limit_line": "net.ipv4.tcp_challenge_ack_limit = 100",
			"error_key": "KERNEL_CVE_2016_5696_URGENT",
			"vulnerable_kernel": "3.10.0-123.el7",
			"sysctl_conf_ack_limit": "100",
			"sysctl_conf_ack_limit_line": "net.ipv4.tcp_challenge_ack_limit=100",
			"mitigation_live": "no"
		},
		"id": 766342155,
		"rule_id": "CVE_2016_5696_kernel|KERNEL_CVE_2016_5696_URGENT",
		"system_id": "f31b6265939d4a8492d3ce9655dc94be",
		"account_number": "540155",
		"uuid": "d195e3c5e5e6469781c4e59fa3f5ba87",
		"date": "2017-05-25T14:01:19.000Z",
		"rule": {
			"summary_html": "<p>A flaw in the Linux kernel&#39;s TCP/IP networking subsystem implementation of the <a href=\"https://tools.ietf.org/html/rfc5961\">RFC 5961</a> challenge ACK rate limiting was found that could allow an attacker located on different subnet to inject or take over a TCP connection between a server and client without needing to use a traditional man-in-the-middle (MITM) attack.</p>\n",
			"generic_html": "<p>A flaw was found in the implementation of the Linux kernel&#39;s handling of networking challenge ack &#40;<a href=\"https://tools.ietf.org/html/rfc5961\">RFC 5961</a>&#41; where an attacker is able to determine the\nshared counter. This flaw allows an attacker located on different subnet to inject or take over a TCP connection between a server and client without needing to use a traditional man-in-the-middle (MITM) attack. </p>\n<p>Red Hat recommends that you update the kernel package or apply mitigations.</p>\n",
			"more_info_html": "<ul>\n<li>For more information about the flaw see <a href=\"https://access.redhat.com/security/cve/CVE-2016-5696\">CVE-2016-5696</a></li>\n<li>To learn how to upgrade packages, see &quot;<a href=\"https://access.redhat.com/solutions/9934\">What is yum and how do I use it?</a>&quot;</li>\n<li>The Customer Portal page for the <a href=\"https://access.redhat.com/security/\">Red Hat Security Team</a> contains more information about policies, procedures, and alerts for Red Hat Products.</li>\n<li>The Security Team also maintains a frequently updated blog at <a href=\"https://securityblog.redhat.com\">securityblog.redhat.com</a>.</li>\n</ul>\n",
			"severity": "ERROR",
			"ansible": true,
			"ansible_fix": false,
			"ansible_mitigation": false,
			"rule_id": "CVE_2016_5696_kernel|KERNEL_CVE_2016_5696_URGENT",
			"error_key": "KERNEL_CVE_2016_5696_URGENT",
			"plugin": "CVE_2016_5696_kernel",
			"description": "Kernel vulnerable to man-in-the-middle via payload injection",
			"summary": "A flaw in the Linux kernel's TCP/IP networking subsystem implementation of the [RFC 5961](https://tools.ietf.org/html/rfc5961) challenge ACK rate limiting was found that could allow an attacker located on different subnet to inject or take over a TCP connection between a server and client without needing to use a traditional man-in-the-middle (MITM) attack.",
			"generic": "A flaw was found in the implementation of the Linux kernel's handling of networking challenge ack &#40;[RFC 5961](https://tools.ietf.org/html/rfc5961)&#41; where an attacker is able to determine the\nshared counter. This flaw allows an attacker located on different subnet to inject or take over a TCP connection between a server and client without needing to use a traditional man-in-the-middle (MITM) attack. \n\nRed Hat recommends that you update the kernel package or apply mitigations.",
			"reason": "<p>A flaw was found in the implementation of the Linux kernel&#39;s handling of networking challenge ack &#40;<a href=\"https://tools.ietf.org/html/rfc5961\">RFC 5961</a>&#41; where an attacker is able to determine the\nshared counter. This flaw allows an attacker located on different subnet to inject or take over a TCP connection between a server and client without needing to use a traditional man-in-the-middle (MITM) attack.</p>\n<p>This host is affected because it is running kernel <strong>3.10.0-123.el7</strong>. </p>\n<p>Your currently loaded kernel configuration contains this setting: </p>\n<pre><code>net.ipv4.tcp_challenge_ack_limit = 100\n</code></pre><p>Your currently stored kernel configuration is: </p>\n<pre><code>net.ipv4.tcp_challenge_ack_limit=100\n</code></pre><p>There is currently no mitigation applied and your system is vulnerable.</p>\n",
			"type": null,
			"more_info": "* For more information about the flaw see [CVE-2016-5696](https://access.redhat.com/security/cve/CVE-2016-5696)\n* To learn how to upgrade packages, see \"[What is yum and how do I use it?](https://access.redhat.com/solutions/9934)\"\n* The Customer Portal page for the [Red Hat Security Team](https://access.redhat.com/security/) contains more information about policies, procedures, and alerts for Red Hat Products.\n* The Security Team also maintains a frequently updated blog at [securityblog.redhat.com](https://securityblog.redhat.com).",
			"active": true,
			"node_id": "2438571",
			"category": "Security",
			"retired": false,
			"reboot_required": false,
			"publish_date": "2016-10-31T04:08:32.000Z",
			"rec_impact": 4,
			"rec_likelihood": 2,
			"resolution": "<p>Red Hat recommends that you update the <code>kernel</code> package and restart the system:</p>\n<pre><code># yum update kernel\n# reboot\n</code></pre><p><strong>or</strong></p>\n<p>Alternatively, this issue can be addressed by applying the following mitigations until the machine is restarted with the updated kernel package.</p>\n<p>Edit <code>/etc/sysctl.conf</code> file as root, add the mitigation configuration, and reload the kernel configuration:</p>\n<pre><code># echo &quot;net.ipv4.tcp_challenge_ack_limit = 2147483647&quot; &gt;&gt; /etc/sysctl.conf \n# sysctl -p\n</code></pre>"
		},
		"maintenance_actions": [{
			"done": false,
			"id": 56045,
			"maintenance_plan": {
				"maintenance_id": 15875,
				"name": "Payload Injection Fix",
				"description": "",
				"start": "2017-06-01T02:00:00.000Z",
				"end": "2017-06-01T03:00:00.000Z",
				"created_by": "rhn-support-wnix",
				"silenced": false,
				"hidden": false,
				"suggestion": null,
				"remote_branch": null
			}
		}, {
			"done": false,
			"id": 61575,
			"maintenance_plan": {
				"maintenance_id": 16825,
				"name": "Summit 2017 Plan 1",
				"description": "",
				"start": null,
				"end": null,
				"created_by": "rhn-support-wnix",
				"silenced": false,
				"hidden": false,
				"suggestion": null,
				"remote_branch": null
			}
		}, {
			"done": false,
			"id": 66175,
			"maintenance_plan": {
				"maintenance_id": 19435,
				"name": null,
				"description": null,
				"start": null,
				"end": null,
				"created_by": "rhn-support-wnix",
				"silenced": false,
				"hidden": false,
				"suggestion": null,
				"remote_branch": null
			}
		}, {
			"done": false,
			"id": 71015,
			"maintenance_plan": {
				"maintenance_id": 19835,
				"name": "Optum Payload",
				"description": "",
				"start": "2017-05-27T02:00:00.000Z",
				"end": "2017-05-27T03:00:00.000Z",
				"created_by": "rhn-support-wnix",
				"silenced": false,
				"hidden": false,
				"suggestion": null,
				"remote_branch": null
			}
		}]
	},
    {
       "details": {
           "mod_loading_disabled": null,
           "package_name": "kernel",
           "error_key": "KERNEL_CVE_2017_2636",
           "vulnerable_kernel": "3.10.0-123.el7",
           "mod_loaded": null,
           "mitigation_info": false
       },
       "id": 766342165,
       "rule_id": "CVE_2017_2636_kernel|KERNEL_CVE_2017_2636",
       "system_id": "f31b6265939d4a8492d3ce9655dc94be",
       "account_number": "540155",
       "uuid": "d195e3c5e5e6469781c4e59fa3f5ba87",
       "date": "2017-05-25T14:01:19.000Z",
       "rule": {
           "summary_html": "<p>A vulnerability in the Linux kernel allowing local privilege escalation was discovered.\nThe issue was reported as <a href=\"https://access.redhat.com/security/cve/CVE-2017-2636\">CVE-2017-2636</a>.</p>\n",
           "generic_html": "<p>A use-after-free flaw was found in the Linux kernel implementation of the HDLC (High-Level Data Link Control) TTY line discipline implementation. It has been assigned CVE-2017-2636.</p>\n<p>An unprivileged local user could use this flaw to execute arbitrary code in kernel memory and increase their privileges on the system. The kernel uses a TTY subsystem to take and show terminal output to connected systems. An attacker crafting specific-sized memory allocations could abuse this mechanism to place a kernel function pointer with malicious instructions to be executed on behalf of the attacker.</p>\n<p>An attacker must have access to a local account on the system; this is not a remote attack. Exploiting this flaw does not require Microgate or SyncLink hardware to be in use.</p>\n<p>Red Hat recommends that you use the proposed mitigation to disable the N_HDLC module.</p>\n",
           "more_info_html": "<ul>\n<li>For more information about the flaw, see <a href=\"https://access.redhat.com/security/cve/CVE-2017-2636\">CVE-2017-2636</a> and <a href=\"https://access.redhat.com/security/vulnerabilities/CVE-2017-2636\">CVE-2017-2636 article</a>.</li>\n<li>The Customer Portal page for the <a href=\"https://access.redhat.com/security/\">Red Hat Security Team</a> contains more information about policies, procedures, and alerts for Red Hat products.</li>\n<li>The Security Team also maintains a frequently updated blog at <a href=\"https://securityblog.redhat.com\">securityblog.redhat.com</a>.</li>\n</ul>\n",
           "severity": "WARN",
           "ansible": true,
           "ansible_fix": false,
           "ansible_mitigation": false,
           "rule_id": "CVE_2017_2636_kernel|KERNEL_CVE_2017_2636",
           "error_key": "KERNEL_CVE_2017_2636",
           "plugin": "CVE_2017_2636_kernel",
           "description": "Kernel vulnerable to local privilege escalation via n_hdlc module (CVE-2017-2636)",
           "summary": "A vulnerability in the Linux kernel allowing local privilege escalation was discovered.\nThe issue was reported as [CVE-2017-2636](https://access.redhat.com/security/cve/CVE-2017-2636).\n",
           "generic": "A use-after-free flaw was found in the Linux kernel implementation of the HDLC (High-Level Data Link Control) TTY line discipline implementation. It has been assigned CVE-2017-2636.\n\nAn unprivileged local user could use this flaw to execute arbitrary code in kernel memory and increase their privileges on the system. The kernel uses a TTY subsystem to take and show terminal output to connected systems. An attacker crafting specific-sized memory allocations could abuse this mechanism to place a kernel function pointer with malicious instructions to be executed on behalf of the attacker.\n\nAn attacker must have access to a local account on the system; this is not a remote attack. Exploiting this flaw does not require Microgate or SyncLink hardware to be in use.\n\nRed Hat recommends that you use the proposed mitigation to disable the N_HDLC module.\n",
           "reason": "<p>A use-after-free flaw was found in the Linux kernel implementation of the HDLC (High-Level Data Link Control) TTY line discipline implementation.</p>\n<p>This host is affected because it is running kernel <strong>3.10.0-123.el7</strong>.</p>\n",
           "type": null,
           "more_info": "* For more information about the flaw, see [CVE-2017-2636](https://access.redhat.com/security/cve/CVE-2017-2636) and [CVE-2017-2636 article](https://access.redhat.com/security/vulnerabilities/CVE-2017-2636).\n* The Customer Portal page for the [Red Hat Security Team](https://access.redhat.com/security/) contains more information about policies, procedures, and alerts for Red Hat products.\n* The Security Team also maintains a frequently updated blog at [securityblog.redhat.com](https://securityblog.redhat.com).\n",
           "active": true,
           "node_id": null,
           "category": "Security",
           "retired": false,
           "reboot_required": false,
           "publish_date": null,
           "rec_impact": 2,
           "rec_likelihood": 2,
           "resolution": "<p>Red Hat recommends updating the <code>kernel</code> package and rebooting the system.</p>\n<pre><code># yum update kernel\n# reboot\n</code></pre>"
       },
       "maintenance_actions": [{
           "done": false,
           "id": 58335,
           "maintenance_plan": {
               "maintenance_id": 16545,
               "name": "Insights Summit 2017 - n_HDLC",
               "description": "",
               "start": "2017-05-06T02:00:00.000Z",
               "end": "2017-05-06T03:00:00.000Z",
               "created_by": "rhn-support-wnix",
               "silenced": false,
               "hidden": false,
               "suggestion": null,
               "remote_branch": null
           }
       }, {
           "done": false,
           "id": 61895,
           "maintenance_plan": {
               "maintenance_id": 16835,
               "name": "Summit 2017 N_HDLC",
               "description": "",
               "start": null,
               "end": null,
               "created_by": "rhn-support-wnix",
               "silenced": false,
               "hidden": false,
               "suggestion": null,
               "remote_branch": null
           }
       }, {
           "done": false,
           "id": 66225,
           "maintenance_plan": {
               "maintenance_id": 19445,
               "name": "Seattle's Best Plan",
               "description": null,
               "start": null,
               "end": null,
               "created_by": "rhn-support-wnix",
               "silenced": false,
               "hidden": false,
               "suggestion": null,
               "remote_branch": null
           }
       }, {
           "done": false,
           "id": 71075,
           "maintenance_plan": {
               "maintenance_id": 19845,
               "name": "Optum N_HDLC FIX",
               "description": null,
               "start": null,
               "end": null,
               "created_by": "rhn-support-wnix",
               "silenced": false,
               "hidden": false,
               "suggestion": null,
               "remote_branch": null
           }
       }]
   }
]
