import React from 'react';
import { t } from '@lingui/macro';
import { useField } from 'formik';
import { Form, FormGroup, Switch } from '@patternfly/react-core';
import styled from 'styled-components';
import LabelSelect from '../../LabelSelect';
import FormField from '../../FormField';
import { TagMultiSelect } from '../../MultiSelect';
import AnsibleSelect from '../../AnsibleSelect';
import { VariablesField } from '../../CodeEditor';
import Popover from '../../Popover';
import { VerbositySelectField } from '../../VerbositySelectField';

const FieldHeader = styled.div`
  display: flex;
  justify-content: space-between;
  padding-bottom: var(--pf-c-form__label--PaddingBottom);

  label {
    --pf-c-form__label--PaddingBottom: 0px;
  }
`;

function OtherPromptsStep({ launchConfig, variablesMode, onVarModeChange }) {
  return (
    <Form
      onSubmit={(e) => {
        e.preventDefault();
      }}
    >
      {launchConfig.ask_job_type_on_launch && <JobTypeField />}
      {launchConfig.ask_scm_branch_on_launch && (
        <FormField
          id="prompt-scm-branch"
          name="scm_branch"
          label={t`Source Control Branch`}
          tooltip={t`Select a branch for the workflow. This branch is applied to all job template nodes that prompt for a branch`}
        />
      )}
      {launchConfig.ask_labels_on_launch && <LabelsField />}
      {launchConfig.ask_forks_on_launch && (
        <FormField
          id="prompt-forks"
          name="forks"
          label={t`Forks`}
          type="number"
          min="0"
        />
      )}
      {launchConfig.ask_limit_on_launch && (
        <FormField
          id="prompt-limit"
          name="limit"
          label={t`Limit`}
          tooltip={t`Provide a host pattern to further constrain the list
          of hosts that will be managed or affected by the playbook. Multiple
          patterns are allowed. Refer to Ansible documentation for more
          information and examples on patterns.`}
        />
      )}
      {launchConfig.ask_verbosity_on_launch && <VerbosityField />}
      {launchConfig.ask_job_slice_count_on_launch && (
        <FormField
          id="prompt-job-slicing"
          name="job_slice_count"
          label={t`Job Slicing`}
          type="number"
          min="1"
        />
      )}
      {launchConfig.ask_timeout_on_launch && (
        <FormField
          id="prompt-timeout"
          name="timeout"
          label={t`Timeout`}
          type="number"
          min="0"
        />
      )}
      {launchConfig.ask_diff_mode_on_launch && <ShowChangesToggle />}
      {launchConfig.ask_tags_on_launch && (
        <TagField
          id="prompt-job-tags"
          name="job_tags"
          label={t`Job Tags`}
          aria-label={t`Job Tags`}
          tooltip={t`Tags are useful when you have a large
            playbook, and you want to run a specific part of a play or task.
            Use commas to separate multiple tags. Refer to Ansible Controller
            documentation for details on the usage of tags.`}
        />
      )}
      {launchConfig.ask_skip_tags_on_launch && (
        <TagField
          id="prompt-skip-tags"
          name="skip_tags"
          label={t`Skip Tags`}
          aria-label={t`Skip Tags`}
          tooltip={t`Skip tags are useful when you have a large
            playbook, and you want to skip specific parts of a play or task.
            Use commas to separate multiple tags. Refer to Ansible Controller
            documentation for details on the usage of tags.`}
        />
      )}
      {launchConfig.ask_variables_on_launch && (
        <VariablesField
          id="prompt-variables"
          name="extra_vars"
          label={t`Variables`}
          initialMode={variablesMode}
          onModeChange={onVarModeChange}
        />
      )}
    </Form>
  );
}

function JobTypeField() {
  const [field, meta, helpers] = useField('job_type');
  const options = [
    {
      value: '',
      key: '',
      label: t`Choose a job type`,
      isDisabled: true,
    },
    { value: 'run', key: 'run', label: t`Run`, isDisabled: false },
    {
      value: 'check',
      key: 'check',
      label: t`Check`,
      isDisabled: false,
    },
  ];
  const isValid = !(meta.touched && meta.error);
  return (
    <FormGroup
      fieldId="propmt-job-type"
      label={t`Job Type`}
      labelIcon={
        <Popover
          content={t`For job templates, select run to execute the playbook.
      Select check to only check playbook syntax, test environment setup,
      and report problems without executing the playbook.`}
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

function VerbosityField() {
  const [, meta] = useField('verbosity');
  const isValid = !(meta.touched && meta.error);

  return (
    <VerbositySelectField
      fieldId="prompt-verbosity"
      tooltip={t`Control the level of output ansible
          will produce as the playbook executes.`}
      isValid={isValid ? 'default' : 'error'}
    />
  );
}

function ShowChangesToggle() {
  const [field, , helpers] = useField('diff_mode');
  return (
    <FormGroup fieldId="prompt-show-changes">
      <FieldHeader>
        {' '}
        <label className="pf-c-form__label" htmlFor="prompt-show-changes">
          <span className="pf-c-form__label-text">
            {t`Show Changes`}
            <Popover
              content={t`If enabled, show the changes made
              by Ansible tasks, where supported. This is equivalent to Ansible’s
              --diff mode.`}
            />
          </span>
        </label>
      </FieldHeader>
      <Switch
        aria-label={field.value ? t`On` : t`Off`}
        id="prompt-show-changes"
        label={t`On`}
        labelOff={t`Off`}
        isChecked={field.value}
        onChange={helpers.setValue}
        ouiaId="prompt-show-changes"
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

function LabelsField() {
  const [field, , helpers] = useField('labels');

  return (
    <FormGroup
      fieldId="propmt-labels"
      label={t`Labels`}
      labelIcon={
        <Popover
          content={t`Optional labels that describe this job, such as 'dev' or 'test'. Labels can be used to group and filter completed jobs.`}
        />
      }
    >
      <LabelSelect
        value={field.value}
        onChange={(labels) => helpers.setValue(labels)}
        createText={t`Create`}
        onError={() => {}}
      />
    </FormGroup>
  );
}

export default OtherPromptsStep;
