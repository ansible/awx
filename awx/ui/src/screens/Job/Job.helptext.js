import React from 'react';
import { t } from '@lingui/macro';

const jobHelpText = {
  jobType: t`For job templates, select run to execute the playbook. Select check to only check playbook syntax, test environment setup, and report problems without executing the playbook.`,
  inventory: t`Select the inventory containing the hosts you want this job to manage.`,
  project: t`Select the project containing the playbook you want this job to execute.`,
  executionEnvironment: t`The execution environment that will be used when launching this job template. The resolved execution environment can be overridden by explicitly assigning a different one to this job template.`,
  playbook: t`Select the playbook to be executed by this job.`,
  credentials: t`Select credentials for accessing the nodes this job will be ran against. You can only select one credential of each type. For machine credentials (SSH), checking "Prompt on launch" without selecting credentials will require you to select a machine credential at run time. If you select credentials and check "Prompt on launch", the selected credential(s) become the defaults that can be updated at run time.`,
  labels: t`Optional labels that describe this job template, such as 'dev' or 'test'. Labels can be used to group and filter job templates and completed jobs.`,
  variables: t`Pass extra command line variables to the playbook. This is the -e or --extra-vars command line parameter for ansible-playbook. Provide key/value pairs using either YAML or JSON. Refer to the documentation for example syntax.`,
  limit: t`Provide a host pattern to further constrain the list of hosts that will be managed or affected by the playbook. Multiple patterns are allowed. Refer to Ansible documentation for more information and examples on patterns.`,
  verbosity: t`Control the level of output ansible will produce as the playbook executes.`,
  jobSlicing: t`Divide the work done by this job template into the specified number of job slices, each running the same tasks against a portion of the inventory.`,
  timeout: t`The amount of time (in seconds) to run before the job is canceled. Defaults to 0 for no job timeout.`,
  instanceGroups: t`Select the Instance Groups for this Job Template to run on.`,
  jobTags: t`Tags are useful when you have a large playbook, and you want to run a specific part of a play or task. Use commas to separate multiple tags. Refer to the documentation for details on the usage of tags.`,
  skipTags: t`Skip tags are useful when you have a large playbook, and you want to skip specific parts of a play or task. Use commas to separate multiple tags. Refer to the documentation for details on the usage of tags.`,
  sourceControlBranch: t`Select a branch for the workflow. This branch is applied to all job template nodes that prompt for a branch.`,
  projectUpdate: t`Project checkout results`,
  forks: (
    <span>
      {t`The number of parallel or simultaneous processes to use while executing the playbook. An empty value, or a value less than 1 will use the Ansible default which is usually 5. The default number of forks can be overwritten with a change to`}{' '}
      <code>ansible.cfg</code>.{' '}
      {t`Refer to the Ansible documentation for details about the configuration file.`}
    </span>
  ),
  module: (moduleName) =>
    moduleName ? (
      <>
        {t`These arguments are used with the specified module. You can find information about ${moduleName} by clicking `}{' '}
        <a
          href={`https://docs.ansible.com/ansible/latest/modules/${moduleName}_module.html`}
          target="_blank"
          rel="noopener noreferrer"
        >
          {t`here.`}
        </a>
      </>
    ) : (
      t`These arguments are used with the specified module.`
    ),
};

export default jobHelpText;
