export default [
	{
		"details": {
			"vulnerable_setting": "hosts:      files dns",
			"affected_package": "glibc-2.17-55.el7",
			"error_key": "GLIBC_CVE_2015_7547"
		},
		"id": 709784455,
		"rule_id": "CVE_2015_7547_glibc|GLIBC_CVE_2015_7547",
		"system_id": "f31b6265939d4a8492d3ce9655dc94be",
		"account_number": "540155",
		"uuid": "d195e3c5e5e6469781c4e59fa3f5ba87",
		"date": "2017-05-25T14:01:19.000Z",
		"rule": {
			"summary_html": "<p>A critical security flaw in the <code>glibc</code> library was found. It allows an attacker to crash an application built against that library or, potentially, execute arbitrary code with privileges of the user running the application.</p>\n",
			"generic_html": "<p>The <code>glibc</code> library is vulnerable to a stack-based buffer overflow security flaw. A remote attacker could create specially crafted DNS responses that could cause the <code>libresolv</code> part of the library, which performs dual A/AAAA DNS queries, to crash or potentially execute code with the permissions of the user running the library. The issue is only exposed when <code>libresolv</code> is called from the nss_dns NSS service module. This flaw is known as <a href=\"https://access.redhat.com/security/cve/CVE-2015-7547\">CVE-2015-7547</a>.</p>\n",
			"more_info_html": "<ul>\n<li>For more information about the flaw see <a href=\"https://access.redhat.com/security/cve/CVE-2015-7547\">CVE-2015-7547</a>.</li>\n<li>To learn how to upgrade packages, see &quot;<a href=\"https://access.redhat.com/solutions/9934\">What is yum and how do I use it?</a>&quot;</li>\n<li>The Customer Portal page for the <a href=\"https://access.redhat.com/security/\">Red Hat Security Team</a> contains more information about policies, procedures, and alerts for Red Hat Products.</li>\n<li>The Security Team also maintains a frequently updated blog at <a href=\"https://securityblog.redhat.com\">securityblog.redhat.com</a>.</li>\n</ul>\n",
			"severity": "ERROR",
			"ansible": true,
			"ansible_fix": false,
			"ansible_mitigation": false,
			"rule_id": "CVE_2015_7547_glibc|GLIBC_CVE_2015_7547",
			"error_key": "GLIBC_CVE_2015_7547",
			"plugin": "CVE_2015_7547_glibc",
			"description": "Remote code execution vulnerability in libresolv via crafted DNS response (CVE-2015-7547)",
			"summary": "A critical security flaw in the `glibc` library was found. It allows an attacker to crash an application built against that library or, potentially, execute arbitrary code with privileges of the user running the application.",
			"generic": "The `glibc` library is vulnerable to a stack-based buffer overflow security flaw. A remote attacker could create specially crafted DNS responses that could cause the `libresolv` part of the library, which performs dual A/AAAA DNS queries, to crash or potentially execute code with the permissions of the user running the library. The issue is only exposed when `libresolv` is called from the nss_dns NSS service module. This flaw is known as [CVE-2015-7547](https://access.redhat.com/security/cve/CVE-2015-7547).",
			"reason": "<p>This host is vulnerable because it has vulnerable package <strong>glibc-2.17-55.el7</strong> installed and DNS is enabled in <code>/etc/nsswitch.conf</code>:</p>\n<pre><code>hosts:      files dns\n</code></pre><p>The <code>glibc</code> library is vulnerable to a stack-based buffer overflow security flaw. A remote attacker could create specially crafted DNS responses that could cause the <code>libresolv</code> part of the library, which performs dual A/AAAA DNS queries, to crash or potentially execute code with the permissions of the user running the library. The issue is only exposed when <code>libresolv</code> is called from the nss_dns NSS service module. This flaw is known as <a href=\"https://access.redhat.com/security/cve/CVE-2015-7547\">CVE-2015-7547</a>.</p>\n",
			"type": null,
			"more_info": "* For more information about the flaw see [CVE-2015-7547](https://access.redhat.com/security/cve/CVE-2015-7547).\n* To learn how to upgrade packages, see \"[What is yum and how do I use it?](https://access.redhat.com/solutions/9934)\"\n* The Customer Portal page for the [Red Hat Security Team](https://access.redhat.com/security/) contains more information about policies, procedures, and alerts for Red Hat Products.\n* The Security Team also maintains a frequently updated blog at [securityblog.redhat.com](https://securityblog.redhat.com).",
			"active": true,
			"node_id": "2168451",
			"category": "Security",
			"retired": false,
			"reboot_required": false,
			"publish_date": "2016-10-31T04:08:35.000Z",
			"rec_impact": 4,
			"rec_likelihood": 2,
			"resolution": "<p>Red Hat recommends updating <code>glibc</code> and restarting the affected system:</p>\n<pre><code># yum update glibc\n# reboot\n</code></pre><p>Alternatively, you can restart all affected services, but because this vulnerability affects a large amount of applications on the system, the best solution is to restart the system.</p>\n"
		},
		"maintenance_actions": []
	},  {
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
	}
]
