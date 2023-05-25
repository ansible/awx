import React from 'react';
import { t } from '@lingui/macro';

const wfHelpTextStrings = () => ({
  inventory: t`Select an inventory for the workflow. This inventory is applied to all workflow nodes that prompt for an inventory.`,
  limit: t`Provide a host pattern to further constrain
  the list of hosts that will be managed or affected by the
  playbook. Multiple patterns are allowed. Refer to Ansible
  documentation for more information and examples on patterns.`,
  sourceControlBranch: t`Select a branch for the workflow. This branch is applied to all job template nodes that prompt for a branch.`,
  labels: t`Optional labels that describe this workflow job template,
  such as 'dev' or 'test'. Labels can be used to group and filter
  workflow job templates and completed jobs.`,
  variables: t`Pass extra command line variables to the playbook. This is the -e or --extra-vars command line parameter for ansible-playbook. Provide key/value pairs using either YAML or JSON. Refer to the Ansible Controller documentation for example syntax.`,
  enableWebhook: t`Enable Webhook for this workflow job template.`,
  enableConcurrentJobs: t`If enabled, simultaneous runs of this workflow job template will be allowed.`,
  webhookURL: t`Webhook services can launch jobs with this workflow job template by making a POST request to this URL.`,
  webhookKey: t`Webhook services can use this as a shared secret.`,
  webhookCredential: t`Optionally select the credential to use to send status updates back to the webhook service.`,
  webhookService: t`Select a webhook service.`,
  jobTags: t`Tags are useful when you have a large playbook, and you want to run a specific part of a play or task. Use commas to separate multiple tags. Refer to the documentation for details on the usage of tags.`,
  skipTags: t`Skip tags are useful when you have a large playbook, and you want to skip specific parts of a play or task. Use commas to separate multiple tags. Refer to the documentation for details on the usage of tags.`,
  enabledOptions: (
    <>
      <p>{t`Concurrent jobs: If enabled, simultaneous runs of this workflow job template will be allowed.`}</p>
      <p>{t`Webhooks: Enable Webhook for this workflow job template.`}</p>
    </>
  ),
  jobNameTemplate: t`A jinja2 template to give the name of a job launched by this job template. Defaults to the name of the job template. You can reference the job object by {{ job.X }} and the extra_vars by {{ extra_vars.Y }}. Note, only values at the creation time of the job are available. For example, job.work_unit_id is populated after the job launch and would not be available as a field.`,
});

export default wfHelpTextStrings;
