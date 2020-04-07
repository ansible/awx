import React from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { useField } from 'formik';
import { FormGroup } from '@patternfly/react-core';
import FormField, { FieldTooltip } from '@components/FormField';
import { TagMultiSelect } from '@components/MultiSelect';
import AnsibleSelect from '@components/AnsibleSelect';
import { VariablesField } from '@components/CodeMirrorInput';

function OtherPromptsStep({ config, i18n }) {
  return (
    <>
      {config.ask_job_type_on_launch && (
        <FormField
          id="prompt-job-type"
          name="job_type"
          label={i18n._(t`Job Type`)}
          tooltip={i18n._(t`For job templates, select run to execute the playbook.
        Select check to only check playbook syntax, test environment setup,
        and report problems without executing the playbook.`)}
        />
      )}
      {config.ask_limit_on_launch && (
        <FormField
          id="prompt-limit"
          name="limit"
          label={i18n._(t`Limit`)}
          tooltip={i18n._(t`Provide a host pattern to further constrain the list
          of hosts that will be managed or affected by the playbook. Multiple
          patterns are allowed. Refer to Ansible documentation for more
          information and examples on patterns.`)}
        />
      )}
      {config.ask_verbosity_on_launch && <VerbosityField i18n={i18n} />}
      {/* TODO: Show Changes toggle? */}
      {config.ask_tags_on_launch && (
        <TagField
          id="prompt-job-tags"
          name="job_tags"
          label={i18n._(t`Job Tags`)}
          tooltip={i18n._(t`Tags are useful when you have a large
            playbook, and you want to run a specific part of a play or task.
            Use commas to separate multiple tags. Refer to Ansible Tower
            documentation for details on the usage of tags.`)}
        />
      )}
      {config.ask_skip_tags_on_launch && (
        <TagField
          id="prompt-skip-tags"
          name="skip_tags"
          label={i18n._(t`Skip Tags`)}
          tooltip={i18n._(t`Skip tags are useful when you have a large
            playbook, and you want to skip specific parts of a play or task.
            Use commas to separate multiple tags. Refer to Ansible Tower
            documentation for details on the usage of tags.`)}
        />
      )}
      {config.ask_variables_on_launch && (
        <VariablesField
          id="prompt-variables"
          name="extra_vars"
          label={i18n._(t`Variables`)}
          promptId="prompt-ask-variables-on-launch"
        />
      )}
    </>
  );
}

function VerbosityField({ i18n }) {
  const [field, meta] = useField('verbosity');
  const options = [
    { value: '0', key: '0', label: i18n._(t`0 (Normal)`) },
    { value: '1', key: '1', label: i18n._(t`1 (Verbose)`) },
    { value: '2', key: '2', label: i18n._(t`2 (More Verbose)`) },
    { value: '3', key: '3', label: i18n._(t`3 (Debug)`) },
    { value: '4', key: '4', label: i18n._(t`4 (Connection Debug)`) },
  ];
  const isValid = !(meta.touched && meta.error);

  return (
    <FormGroup
      fieldId="prompt-verbosity"
      isValid={isValid}
      label={i18n._(t`Verbosity`)}
    >
      <FieldTooltip
        content={i18n._(t`Control the level of output ansible
          will produce as the playbook executes.`)}
      />
      <AnsibleSelect id="prompt-verbosity" data={options} {...field} />
    </FormGroup>
  );
}

function TagField({ id, name, label, tooltip }) {
  const [field, , helpers] = useField(name);
  return (
    <FormGroup fieldId={id} label={label}>
      <FieldTooltip content={tooltip} />
      <TagMultiSelect value={field.value} onChange={helpers.setValue} />
    </FormGroup>
  );
}

/*
  tooltips:
  verbosity: Control the level of output ansible will produce as the playbook executes.
  job tags: Tags are useful when you have a large playbook, and you want to run a specific part of a play or task. Use commas to separate multiple tags. Refer to Ansible Tower documentation for details on the usage of tags.
  skip tags: Skip tags are useful when you have a large playbook, and you want to skip specific parts of a play or task. Use commas to separate multiple tags. Refer to Ansible Tower documentation for details on the usage of tags.
  show changes: If enabled, show the changes made by Ansible tasks, where supported. This is equivalent to Ansible’s --diff mode.
  extra variables: Pass extra command line variables to the playbook. This is the -e or --extra-vars command line parameter for ansible-playbook. Provide key/value pairs using either YAML or JSON.

  JSON:
  {
  "somevar": "somevalue",
  "password": "magic"
  }
  YAML:
  ---
  somevar: somevalue
  password: magic
*/

export default withI18n()(OtherPromptsStep);
