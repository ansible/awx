# Changelog

This is a list of high-level changes for each release of AWX. A full list of commits can be found at `https://github.com/ansible/awx/releases/tag/<version>`.

## 10.0.0 (Mar 30, 2020)
- As of AWX 10.0.0, the official AWX CLI no longer supports Python 2 (it requires at least Python 3.6) (https://github.com/ansible/awx/pull/6327)
- AWX no longer relies on RabbitMQ; Redis is added as a new dependency (https://github.com/ansible/awx/issues/5443)
- Altered AWX's event tables to allow more than ~2 billion total events (https://github.com/ansible/awx/issues/6010)
- Improved the performance (time to execute, and memory consumption) of the periodic job cleanup system job (https://github.com/ansible/awx/pull/6166)
- Updated Job Templates so they now have an explicit Organization field (it is no longer inferred from the associated Project) (https://github.com/ansible/awx/issues/3903)
- Updated social-auth-core to address an upcoming GitHub API deprecation (https://github.com/ansible/awx/issues/5970)
- Updated to ansible-runner 1.4.6 to address various bugs.
- Updated Django to address CVE-2020-9402
- Updated pyyaml version to address CVE-2017-18342
- Fixed a bug which prevented the new `scm_branch` field from being used in custom notification templates (https://github.com/ansible/awx/issues/6258)
- Fixed a race condition that sometimes causes success/failure notifications to include an incomplete list of hosts (https://github.com/ansible/awx/pull/6290)
- Fixed a bug that can cause certain setting pages to lose unsaved form edits when a playbook is launched (https://github.com/ansible/awx/issues/5265)
- Fixed a bug that can prevent the "Use TLS/SSL" field from properly saving when editing email notification templates (https://github.com/ansible/awx/issues/6383)
- Fixed a race condition that sometimes broke event/stdout processing for jobs launched in container groups (https://github.com/ansible/awx/issues/6280)

## 9.3.0 (Mar 12, 2020)
- Added the ability to specify an OAuth2 token description in the AWX CLI (https://github.com/ansible/awx/issues/6122)
- Added support for K8S service account annotations to the installer (https://github.com/ansible/awx/pull/6007)
- Added support for K8S imagePullSecrets to the installer (https://github.com/ansible/awx/pull/5989)
- Launching jobs (and workflows) using the --monitor flag in the AWX CLI now returns a non-zero exit code on job failure (https://github.com/ansible/awx/issues/5920)
- Improved UI performance for various job views when many simultaneous users are logged into AWX (https://github.com/ansible/awx/issues/5883)
- Updated to the latest version of Django to address a few open CVEs (https://github.com/ansible/awx/pull/6080)
- Fixed a critical bug which can cause AWX to hang and stop launching playbooks after a periodic of time (https://github.com/ansible/awx/issues/5617)
- Fixed a bug which caused delays in project update stdout for certain large SCM clones (as of Ansible 2.9+) (https://github.com/ansible/awx/pull/6254)
- Fixed a bug which caused certain smart inventory filters to mistakenly return duplicate hosts (https://github.com/ansible/awx/pull/5972)
- Fixed an unclear server error when creating smart inventories with the AWX collection (https://github.com/ansible/awx/issues/6250)
- Fixed a bug that broke Grafana notification support (https://github.com/ansible/awx/issues/6137)
- Fixed a UI bug which prevent users with read access to an organization from editing credentials for that organization (https://github.com/ansible/awx/pull/6241)
- Fixed a bug which prevent workflow approval records from recording a `started` and `elapsed` date (https://github.com/ansible/awx/issues/6202)
- Fixed a bug which caused workflow nodes to have a confusing option for `verbosity` (https://github.com/ansible/awx/issues/6196)
- Fixed an RBAC bug which prevented projects and inventory schedules from being created by certain users in certain contexts (https://github.com/ansible/awx/issues/5717)
- Fixed a bug that caused `role_path` in a project's config to not be respected due to an error processing `/etc/ansible/ansible.cfg` (https://github.com/ansible/awx/pull/6038)
- Fixed a bug that broke inventory updates for installs with custom home directories for the awx user (https://github.com/ansible/awx/pull/6152)
- Fixed a bug that broke fact data collection when AWX encounters invalid/unexpected fact data (https://github.com/ansible/awx/issues/5935)


## 9.2.0 (Feb 12, 2020)
- Added the ability to configure the convergence behavior of workflow nodes https://github.com/ansible/awx/issues/3054
- AWX now allows for a configurable global limit for fork count (per-job run).  The default maximum is 200. https://github.com/ansible/awx/pull/5604
- Added the ability to specify AZURE_PUBLIC_CLOUD (for e.g., Azure Government KeyVault support) for the Azure credential plugin https://github.com/ansible/awx/issues/5138
- Added support for several additional parameters for Satellite dynamic inventory https://github.com/ansible/awx/pull/5598
- Added a new field to jobs for tracking the date/time a job is cancelled https://github.com/ansible/awx/pull/5610
- Made a series of additional optimizations to the callback receiver to further improve stdout write speed for running playbooks https://github.com/ansible/awx/pull/5677 https://github.com/ansible/awx/pull/5739
- Updated AWX to be compatible with Helm 3.x (https://github.com/ansible/awx/pull/5776)
- Optimized AWX's job dependency/scheduling code to drastically improve processing time in scenarios where there are many pending jobs scheduled simultaneously https://github.com/ansible/awx/issues/5154
- Fixed a bug which could cause SCM authentication details (basic auth passwords) to be reported to external loggers in certain failure scenarios (e.g., when a git clone fails and ansible itself prints an error message to stdout) https://github.com/ansible/awx/pull/5812
- Fixed a k8s installer bug that caused installs to fail in certain situations https://github.com/ansible/awx/issues/5574
- Fixed a number of issues that caused analytics gathering and reporting to run more often than necessary https://github.com/ansible/awx/pull/5721
- Fixed a bug in the AWX CLI that prevented JSON-type settings from saving properly https://github.com/ansible/awx/issues/5528
- Improved support for fetching custom virtualenv dependencies when AWX is installed behind a proxy https://github.com/ansible/awx/pull/5805
- Updated the bundled version of openstacksdk to address a known issue https://github.com/ansible/awx/issues/5821
- Updated the bundled vmware_inventory plugin to the latest version to address a bug https://github.com/ansible/awx/pull/5668
- Fixed a bug that can cause inventory updates to fail to properly save their output when run within a workflow https://github.com/ansible/awx/pull/5666
- Removed a number of pre-computed fields from the Host and Group models to improve AWX performance.  As part of this change, inventory group UIs throughout the interface no longer display status icons https://github.com/ansible/awx/pull/5448 

## 9.1.1 (Jan 14, 2020)

- Fixed a bug that caused database migrations on Kubernetes installs to hang https://github.com/ansible/awx/pull/5579
- Upgraded Python-level app dependencies in AWX virtual environment https://github.com/ansible/awx/pull/5407
- Running jobs no longer block associated inventory updates https://github.com/ansible/awx/pull/5519
- Fixed invalid_response SAML error https://github.com/ansible/awx/pull/5577
- Optimized the callback receiver to drastically improve the write speed of stdout for parallel jobs (https://github.com/ansible/awx/pull/5618)

## 9.1.0 (Dec 17, 2019)
- Added a command to generate a new SECRET_KEY and rekey the secrets in the database
- Removed project update locking when jobs using it are running
- Fixed slow queries for /api/v2/instances and /api/v2/instance_groups when smart inventories are used
- Fixed a partial password disclosure when special characters existed in the RabbitMQ password (CVE-2019-19342)
- Fixed hang in error handling for source control checkouts
- Fixed an error on subsequent job runs that override the branch of a project on an instance that did not have a prior project checkout
- Fixed an issue where jobs launched in isolated or container groups would incorrectly timeout
- Fixed an incorrect link to instance groups documentation in the user interface
- Fixed editing of inventory on Workflow templates
- Fixed multiple issues with OAuth2 token cleanup system jobs
- Fixed a bug that broke email notifications for workflow approval/deny https://github.com/ansible/awx/issues/5401
- Updated SAML implementation to automatically login if authorization already exists
- Updated AngularJS to 1.7.9 for CVE-2019-10768

## 9.0.1 (Nov 4, 2019)

- Fixed a bug in the installer that broke certain types of k8s installs https://github.com/ansible/awx/issues/5205

## 9.0.0 (Oct 31, 2019)

- Updated AWX images to use centos:8 as the parent image.
- Updated to ansible-runner 1.4.4 to address various bugs.
- Added oc and kubectl to the AWX images to support new container-based execution introduced in 8.0.0.
- Added some optimizations to speed up the deletion of large Inventory Groups.
- Fixed a bug that broke webhook launches for Job Templates that define a survey (https://github.com/ansible/awx/issues/5062).
- Fixed a bug in the CLI which incorrectly parsed launch time arguments for `awx job_templates launch` and `awx workflow_job_templates launch` (https://github.com/ansible/awx/issues/5093).
- Fixed a bug that caused inventory updates using "sourced from a project" to stop working (https://github.com/ansible/awx/issues/4750).
- Fixed a bug that caused Slack notifications to sometimes show the wrong bot avatar (https://github.com/ansible/awx/pull/5125).
- Fixed a bug that prevented the use of digits in Tower's URL settings (https://github.com/ansible/awx/issues/5081).

## 8.0.0 (Oct 21, 2019)

- The Ansible Tower Ansible modules have been migrated to a new official Ansible AWX collection: https://galaxy.ansible.com/awx/AWX
  Please note that this functionality is only supported in Ansible 2.9+
- AWX now supports the ability to launch jobs from external webhooks (GitHub and GitLab integration are supported).
- AWX now supports Container Groups, a new feature that allows you to schedule and run playbooks on single-use kubernetes pods on-demand.
- AWX now supports sending notifications when Workflow steps are approved, denied, or time out.
- AWX now records the user who approved or denied Workflow steps.
- AWX now supports fetching Ansible Collections from private galaxy servers.
- AWX now checks the user's ansible.cfg for paths where role/collections may live when running project updates.
- AWX now uses PostgreSQL 10 by default.
- AWX now warns more loudly about underlying AMQP connectivity issues (https://github.com/ansible/awx/pull/4857).
- Added a few optimizations to drastically improve dashboard performance for larger AWX installs (installs with several hundred thousand jobs or more).
- Updated to the latest version of Ansible's VMWare inventory script (which adds support for vmware_guest_facts).
- Deprecated /api/v2/inventory_scripts/ (this endpoint - and the Custom Inventory Script feature - will be removed in a future release of AWX).
- Fixed a bug which prevented Organization Admins from removing users from their own Organization (https://github.com/ansible/awx/issues/2979)
- Fixed a bug which sometimes caused cluster nodes to fail to re-join with a cryptic error, "No instance found with the current cluster host id" (https://github.com/ansible/awx/issues/4294)
- Fixed a bug that prevented the use of launch-time passphrases when using credential plugins (https://github.com/ansible/awx/pull/4807)
- Fixed a bug that caused notifications assigned at the Organization level not to take effect for Workflows in that Organization (https://github.com/ansible/awx/issues/4712)
- Fixed a bug which caused a notable amount of CPU overhead on RabbitMQ health checks (https://github.com/ansible/awx/pull/5009)
- Fixed a bug which sometimes caused the <return> key to stop functioning in <textarea> elements (https://github.com/ansible/awx/issues/4192)
- Fixed a bug which caused request contention when the same OAuth2.0 token was used in multiple simultaneous requests (https://github.com/ansible/awx/issues/4694)
- Fixed a bug related to parsing multiple choice survey options (https://github.com/ansible/awx/issues/4452).
- Fixed a bug that caused single-sign-on icons on the login page to fail to render in certain Windows browsers (https://github.com/ansible/awx/issues/3924)
- Fixed a number of bugs that caused certain OAuth2 settings to not be properly respected, such as REFRESH_TOKEN_EXPIRE_SECONDS.
- Fixed a number of bugs in the AWX CLI, including a bug which sometimes caused long lines of stdout output to be unexpectedly truncated.
- Fixed a number of bugs on the job details UI which sometimes caused auto-scrolling stdout to become stuck.
- Fixed a bug which caused LDAP authentication to fail if the TLD of the server URL contained digits (https://github.com/ansible/awx/issues/3646)
- Fixed a bug which broke HashiCorp Vault integration on older versions of HashiCorp Vault.

## 7.0.0 (Sept 4, 2019)

- AWX now detects and installs Ansible Collections defined in your project (note - this feature only works in Ansible 2.9+) (https://github.com/ansible/awx/issues/2534)
- AWX now includes an official command line client.  Keep an eye out for a follow-up email on this mailing list for information on how to install it and try it out.
- Added the ability to provide a specific SCM branch on jobs (https://github.com/ansible/awx/issues/282)
- Added support for Workflow Approval Nodes, a new feature which allows you to add "pause and wait for approval" steps into your workflows (https://github.com/ansible/awx/issues/1206)
- Added the ability to specify a specific HTTP method for webhook notifications (POST vs PUT) (https://github.com/ansible/awx/pull/4124)
- Added the ability to specify a username and password for HTTP Basic Authorization for webhook notifications (https://github.com/ansible/awx/pull/4124)
- Added support for customizing the text content of notifications (https://github.com/ansible/awx/issues/79)
- Added the ability to enable and disable hosts in dynamic inventory (https://github.com/ansible/awx/pull/4420)
- Added the description (if any) to the Job Template list (https://github.com/ansible/awx/issues/4359)
- Added new metrics for instance hostnames and pending jobs to the /api/v2/metrics/ endpoint (https://github.com/ansible/awx/pull/4375)
- Changed AWX's on/off toggle buttons to a non-text based style to simplify internationalization (https://github.com/ansible/awx/pull/4425)
- Events emitted by ansible for adhoc commands are now sent to the external log aggregrator (https://github.com/ansible/awx/issues/4545)
- Fixed a bug which allowed a user to make an organization credential in another organization without permissions to that organization (https://github.com/ansible/awx/pull/4483)
- Fixed a bug that caused `extra_vars` on workflows to break when edited (https://github.com/ansible/awx/issues/4293)
- Fixed a slow SQL query that caused performance issues when large numbers of groups exist (https://github.com/ansible/awx/issues/4461)
- Fixed a few minor bugs in survey field validation (https://github.com/ansible/awx/pull/4509) (https://github.com/ansible/awx/pull/4479)
- Fixed a bug that sometimes resulted in orphaned `ansible_runner_pi` directories in `/tmp` after playbook execution (https://github.com/ansible/awx/pull/4409)
- Fixed a bug that caused the `is_system_auditor` flag in LDAP configuration to not work (https://github.com/ansible/awx/pull/4396)
- Fixed a bug which caused schedules to disappear from the UI when toggled off (https://github.com/ansible/awx/pull/4378)
- Fixed a bug that sometimes caused stdout content to contain extraneous blank lines in newer versions of Ansible (https://github.com/ansible/awx/pull/4391)
- Updated to the latest Django security release, 2.2.4 (https://github.com/ansible/awx/pull/4410) (https://www.djangoproject.com/weblog/2019/aug/01/security-releases/)
- Updated the default version of git to a version that includes support for x509 certificates (https://github.com/ansible/awx/issues/4362)
- Removed the deprecated `credential` field from `/api/v2/workflow_job_templates/N/` (as part of the `/api/v1/` removal in prior AWX versions - https://github.com/ansible/awx/pull/4490).

## 6.1.0 (Jul 18, 2019)

- Updated AWX to use Django 2.2.2.
- Updated the provided openstacksdk version to support new functionality (such as Nova scheduler_hints)
- Added the ability to specify a custom cacert for the HashiCorp Vault credential plugin
- Fixed a number of bugs related to path lookups for the HashiCorp Vault credential plugin
- Fixed a bug which prevented signed SSH certificates from working, including the HashiCorp Vault Signed SSH backend
- Fixed a bug which prevented custom logos from displaying on the login page (as a result of a new Content Security Policy in 6.0.0)
- Fixed a bug which broke websocket connectivity in Apple Safari (as a result of a new Content Security Policy in 6.0.0)
- Fixed a bug on the job output page that occasionally caused the "up" and "down" buttons to not load additional output
- Fixed a bug on the job output page that caused quoted task names to display incorrectly

## 6.0.0 (Jul 1, 2019)

- Removed support for "Any" notification templates and their API endpoints e.g., /api/v2/job_templates/N/notification_templates/any/ (https://github.com/ansible/awx/issues/4022)
- Fixed a bug which prevented credentials from properly being applied to inventory sources (https://github.com/ansible/awx/issues/4059)
- Fixed a bug which can cause the task dispatcher to hang indefinitely when external logging support (e.g., Splunk, Logstash) is enabled (https://github.com/ansible/awx/issues/4181)
- Fixed a bug which causes slow stdout display when running jobs against smart inventories. (https://github.com/ansible/awx/issues/3106)
- Fixed a bug that caused SSL verification flags to fail to be respected for LDAP authentication in certain environments. (https://github.com/ansible/awx/pull/4190)
- Added a simple Content Security Policy (https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP) to restrict access to third-party resources in the browser. (https://github.com/ansible/awx/pull/4167)
- Updated ovirt4 library dependencies to work with newer versions of oVirt (https://github.com/ansible/awx/issues/4138)

## 5.0.0 (Jun 21, 2019)

- Bump Django Rest Framework from 3.7.7 to 3.9.4
- Bump setuptools / pip dependencies
- Fixed bug where Recent Notification list would not appear
- Added notifications on job start
- Default to Ansible 2.8
