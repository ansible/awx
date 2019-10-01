# Insights Integration
Insights provides remediation playbooks that Tower executes. Tower also provides a view of Insights-discovered misconfigurations and problems via proxying Insights API requests. Credentials to access the Insights API are stored in Tower and can be related to an Inventory in which Insights hosts  are presumed to exist. This same Insights Credential can be attached to a Tower Project. The Tower Project will pull the Insights remediation plans whenever a Project Update runs.


## Tower Insights Credential

Tower has an Insights Credential to store the username and password to be used when accessing the Insights API. The Insights Credential is a new `CredentialType` in the Tower system. The Insights Credential can be associated with an Insights Project and any non-smart Inventory.


## Tower Recognized Insights Host

Tower considers a host an Insights Host when the attribute `insights_system_id` on the host is set to something other than `null`. The `insights_system_id` is used to identify the host in the Insights system when making proxied requests to the Insights API. The `insights_system_id` is set as a result of the fact scan playbook that is running (specifically, as a result of the `scan_insights` Ansible module being called). The `scan_insights` module will read the value from the file `/etc/redhat-access-insights/machine-id` on a host. If found, the value will be assigned to the `insights_system_id` for that host. The host would then be considered an Insights host.


## Tower Insights Proxy

Insights data for a Tower-recognized Insights Host can be acquired from the insights endpoint hanging off of the host detail endpoint. Each time the Insights endpoint has a `GET` request issued to it, the backend issues a request to the Insights API for the `insights_system_id`. The response is then returned in the same get/response cycle. The response contains Insights details for the host including (1) the current plans, (2) reports, and (3) rules.
`/api/v2/hosts/<id>/insights/`


## Tower Insights Project

Tower has a Project exclusively for Insights. Projects of type Insights can attach a special Insights Credential. The Insights Credential is used for accessing the Insights API in the Project Update playbook. The `scm_revision` for an Insights Project differs from traditional SCM backed projects. The `scm_revision` is the Insights `ETag` HTTP header value returned when making a plan requests to the Insights API during a Project update run. The `ETag` communications a version derived from the response data. During a Project Update, the Project's `scm_revision` will be updated with the new `ETag`. The `ETag` will also be written to disk in the Project directory as `.scm_revision`. The Project update will  download the remediation playbooks if the `.scm_revision` does not equal the `ETag`.
