import React from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { useField } from 'formik';
import { Form, FormGroup, Switch } from '@patternfly/react-core';
import styled from 'styled-components';
import FormField from '../../FormField';
import { TagMultiSelect } from '../../MultiSelect';
import AnsibleSelect from '../../AnsibleSelect';
import { VariablesField } from '../../CodeMirrorInput';
import Popover from '../../Popover';

const FieldHeader = styled.div`
  display: flex;
  justify-content: space-between;
  padding-bottom: var(--pf-c-form__label--PaddingBottom);

  label {
    --pf-c-form__label--PaddingBottom: 0px;
  }
`;

function OtherPromptsStep({ config, i18n }) {
  return (
    <Form>
      {config.ask_job_type_on_launch && <JobTypeField i18n={i18n} />}
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
      {config.ask_scm_branch_on_launch && (
        <FormField
          id="prompt-scm-branch"
          name="scm_branch"
          label={i18n._(t`Source Control Branch`)}
          tooltip={i18n._(
            t`Select a branch for the workflow. This branch is applied to all job template nodes that prompt for a branch`
          )}
        />
      )}
      {config.ask_verbosity_on_launch && <VerbosityField i18n={i18n} />}
      {config.ask_diff_mode_on_launch && <ShowChangesToggle i18n={i18n} />}
      {config.ask_tags_on_launch && (
        <TagField
          id="prompt-job-tags"
          name="job_tags"
          label={i18n._(t`Job Tags`)}
          aria-label={i18n._(t`Job Tags`)}
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
          aria-label={i18n._(t`Skip Tags`)}
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
        />
      )}
    </Form>
  );
}

function JobTypeField({ i18n }) {
  const [field, meta, helpers] = useField('job_type');
  const options = [
    {
      value: '',
      key: '',
      label: i18n._(t`Choose a job type`),
      isDisabled: true,
    },
    { value: 'run', key: 'run', label: i18n._(t`Run`), isDisabled: false },
    {
      value: 'check',
      key: 'check',
      label: i18n._(t`Check`),
      isDisabled: false,
    },
  ];
  const isValid = !(meta.touched && meta.error);
  return (
    <FormGroup
      fieldId="propmt-job-type"
      label={i18n._(t`Job Type`)}
      labelIcon={
        <Popover
          content={i18n._(t`For job templates, select run to execute the playbook.
      Select check to only check playbook syntax, test environment setup,
      and report problems without executing the playbook.`)}
        />
      }
      isRequired
      validated={isValid ? 'default' : 'error'}
    >
      <AnsibleSelect
        id="prompt-job-type"
        data={options}
        {...field}
        onChange={(event, value) => helpers.setValue(value)}
      />
    </FormGroup>
  );
}

function VerbosityField({ i18n }) {
  const [field, meta, helpers] = useField('verbosity');
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
      validated={isValid ? 'default' : 'error'}
      label={i18n._(t`Verbosity`)}
      labelIcon={
        <Popover
          content={i18n._(t`Control the level of output ansible
          will produce as the playbook executes.`)}
        />
      }
    >
      <AnsibleSelect
        id="prompt-verbosity"
        data={options}
        {...field}
        onChange={(event, value) => helpers.setValue(value)}
      />
    </FormGroup>
  );
}

function ShowChangesToggle({ i18n }) {
  const [field, , helpers] = useField('diff_mode');
  return (
    <FormGroup fieldId="prompt-show-changes">
      <FieldHeader>
        {' '}
        <label className="pf-c-form__label" htmlFor="prompt-show-changes">
          <span className="pf-c-form__label-text">
            {i18n._(t`Show Changes`)}
            <Popover
              content={i18n._(t`If enabled, show the changes made
              by Ansible tasks, where supported. This is equivalent to Ansible’s
              --diff mode.`)}
            />
          </span>
        </label>
      </FieldHeader>
      <Switch
        aria-label={field.value ? i18n._(t`On`) : i18n._(t`Off`)}
        id="prompt-show-changes"
        label={i18n._(t`On`)}
        labelOff={i18n._(t`Off`)}
        isChecked={field.value}
        onChange={helpers.setValue}
      />
    </FormGroup>
  );
}

function TagField({ id, name, label, tooltip }) {
  const [field, , helpers] = useField(name);
  return (
    <FormGroup
      fieldId={id}
      label={label}
      labelIcon={<Popover content={tooltip} />}
    >
      <TagMultiSelect value={field.value} onChange={helpers.setValue} />
    </FormGroup>
  );
}

export default withI18n()(OtherPromptsStep);
