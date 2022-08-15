import React from 'react';
import { t } from '@lingui/macro';
import getDocsBaseUrl from 'util/getDocsBaseUrl';

const jtHelpTextStrings = () => ({
  jobType: t`For job templates, select run to execute the playbook. Select check to only check playbook syntax, test environment setup, and report problems without executing the playbook.`,
  inventory: t`Select the inventory containing the hosts you want this job to manage.`,
  project: t`Select the project containing the playbook you want this job to execute.`,
  executionEnvironmentForm: t`The container image to be used for execution.`,
  executionEnvironmentDetail: t`The execution environment that will be used when launching this job template. The resolved execution environment can be overridden by explicitly assigning a different one to this job template.`,
  playbook: t`Select the playbook to be executed by this job.`,
  credentials: t`Select credentials for accessing the nodes this job will be ran against. You can only select one credential of each type. For machine credentials (SSH), checking "Prompt on launch" without selecting credentials will require you to select a machine credential at run time. If you select credentials and check "Prompt on launch", the selected credential(s) become the defaults that can be updated at run time.`,
  labels: t`Optional labels that describe this job template, such as 'dev' or 'test'. Labels can be used to group and filter job templates and completed jobs.`,
  variables: t`Pass extra command line variables to the playbook. This is the -e or --extra-vars command line parameter for ansible-playbook. Provide key/value pairs using either YAML or JSON. Refer to the documentation for example syntax.`,
  limit: t`Provide a host pattern to further constrain the list of hosts that will be managed or affected by the playbook. Multiple patterns are allowed. Refer to Ansible documentation for more information and examples on patterns.`,
  verbosity: t`Control the level of output ansible will produce as the playbook executes.`,
  jobSlicing: t`Divide the work done by this job template into the specified number of job slices, each running the same tasks against a portion of the inventory.`,
  timeout: t`The amount of time (in seconds) to run before the job is canceled. Defaults to 0 for no job timeout.`,
  showChanges: t`If enabled, show the changes made by Ansible tasks, where supported. This is equivalent to Ansible's --diff mode.`,
  instanceGroups: t`Select the Instance Groups for this Job Template to run on.`,
  jobTags: t`Tags are useful when you have a large playbook, and you want to run a specific part of a play or task. Use commas to separate multiple tags. Refer to the documentation for details on the usage of tags.`,
  skipTags: t`Skip tags are useful when you have a large playbook, and you want to skip specific parts of a play or task. Use commas to separate multiple tags. Refer to the documentation for details on the usage of tags.`,
  webhookService: t`Select a webhook service.`,
  webhookURL: t`Webhook services can launch jobs with this workflow job template by making a POST request to this URL.`,
  webhookKey: t`Webhook services can use this as a shared secret.`,
  webhookCredential: t`Optionally select the credential to use to send status updates back to the webhook service.`,
  sourceControlBranch: t`Branch to use in job run. Project default used if blank. Only allowed if project allow_override field is set to true.`,
  provisioningCallbacks: (brandName = '') =>
    t`Enables creation of a provisioning callback URL. Using the URL a host can contact ${brandName} and request a configuration update using this job template.`,
  privilegeEscalation: t`If enabled, run this playbook as an administrator.`,
  enableWebhook: t`Enable webhook for this template.`,
  concurrentJobs: t`If enabled, simultaneous runs of this job template will be allowed.`,
  enableFactStorage: t`If enabled, this will store gathered facts so they can be viewed at the host level. Facts are persisted and injected into the fact cache at runtime.`,
  enabledOptions: (
    <>
      <p>{t`Concurrent jobs: If enabled, simultaneous runs of this job template will be allowed.`}</p>
      <p>{t`Fact storage: If enabled, this will store gathered facts so they can be viewed at the host level. Facts are persisted and injected into the fact cache at runtime..`}</p>
      <p>{t`Privilege escalation: If enabled, run this playbook as an administrator.`}</p>
      <p>{t`Provisioning callbacks: Enables creation of a provisioning callback URL. Using the URL a host can contact Ansible AWX and request a configuration update using this job template.`}</p>
      <p>{t`Webhooks: Enable webhook for this template.`}</p>
    </>
  ),
  forks: (
    <span>
      {t`The number of parallel or simultaneous processes to use while executing the playbook. An empty value, or a value less than 1 will use the Ansible default which is usually 5. The default number of forks can be overwritten with a change to`}{' '}
      <code>ansible.cfg</code>.{' '}
      {t`Refer to the Ansible documentation for details about the configuration file.`}
    </span>
  ),
  localTimeZone: (config = '') => (
    <span>
      {t`Refer to the`}{' '}
      <a
        href={`${getDocsBaseUrl(config)}/html/userguide/scheduling.html`}
        target="_blank"
        rel="noreferrer"
      >
        {t`documentation`}
      </a>{' '}
      {t`for more information.`}
    </span>
  ),
});

export default jtHelpTextStrings;
