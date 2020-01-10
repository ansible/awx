# Changelog

This is a list of high-level changes for each release of AWX. A full list of commits can be found at `https://github.com/ansible/awx/releases/tag/<version>`.

## 9.1.1

- Fixed bug that caused database migrations on Kubernetes installs to hang https://github.com/ansible/awx/pull/5579
- Upgrade Python-level app dependencies in AWX virtual environment https://github.com/ansible/awx/pull/5407
- Prevent running jobs from blocking inventory updates https://github.com/ansible/awx/pull/5519
- Fixed invalid_response SAML error https://github.com/ansible/awx/pull/5577
- Started using this changelog https://github.com/ansible/awx/pull/5635
