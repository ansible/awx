# Changelog

This is a list of high-level changes for each release of AWX. A full list of commits can be found at `https://github.com/ansible/awx/releases/tag/<version>`.

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
