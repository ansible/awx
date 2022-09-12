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
import jobHelpText from '../../../screens/Job/Job.helptext';
import workflowHelpText from '../../../screens/Template/shared/WorkflowJobTemplate.helptext';

const FieldHeader = styled.div`
  display: flex;
  justify-content: space-between;
  padding-bottom: var(--pf-c-form__label--PaddingBottom);

  label {
    --pf-c-form__label--PaddingBottom: 0px;
  }
`;

function OtherPromptsStep({ launchConfig, variablesMode, onVarModeChange }) {
  const helpTextSource = launchConfig.job_template_data
    ? jobHelpText
    : workflowHelpText;
  return (
    <Form
      onSubmit={(e) => {
        e.preventDefault();
      }}
    >
      {launchConfig.ask_job_type_on_launch && (
        <JobTypeField helpTextSource={helpTextSource} />
      )}
      {launchConfig.ask_scm_branch_on_launch && (
        <FormField
          id="prompt-scm-branch"
          name="scm_branch"
          label={t`Source Control Branch`}
          tooltip={helpTextSource.sourceControlBranch}
        />
      )}
      {launchConfig.ask_labels_on_launch && (
        <LabelsField helpTextSource={helpTextSource} />
      )}
      {launchConfig.ask_forks_on_launch && (
        <FormField
          id="prompt-forks"
          name="forks"
          label={t`Forks`}
          type="number"
          min="0"
          tooltip={helpTextSource.forks}
        />
      )}
      {launchConfig.ask_limit_on_launch && (
        <FormField
          id="prompt-limit"
          name="limit"
          label={t`Limit`}
          tooltip={helpTextSource.limit}
        />
      )}
      {launchConfig.ask_verbosity_on_launch && (
        <VerbosityField helpTextSource={helpTextSource} />
      )}
      {launchConfig.ask_job_slice_count_on_launch && (
        <FormField
          id="prompt-job-slicing"
          name="job_slice_count"
          label={t`Job Slicing`}
          type="number"
          min="1"
          tooltip={helpTextSource.jobSlicing}
        />
      )}
      {launchConfig.ask_timeout_on_launch && (
        <FormField
          id="prompt-timeout"
          name="timeout"
          label={t`Timeout`}
          type="number"
          min="0"
          tooltip={helpTextSource.timeout}
        />
      )}
      {launchConfig.ask_diff_mode_on_launch && <ShowChangesToggle />}
      {launchConfig.ask_tags_on_launch && (
        <TagField
          id="prompt-job-tags"
          name="job_tags"
          label={t`Job Tags`}
          aria-label={t`Job Tags`}
          tooltip={helpTextSource.jobTags}
        />
      )}
      {launchConfig.ask_skip_tags_on_launch && (
        <TagField
          id="prompt-skip-tags"
          name="skip_tags"
          label={t`Skip Tags`}
          aria-label={t`Skip Tags`}
          tooltip={helpTextSource.skipTags}
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

function JobTypeField({ helpTextSource }) {
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
      fieldId="prompt-job-type"
      label={t`Job Type`}
      labelIcon={<Popover content={helpTextSource.jobType} />}
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

function VerbosityField({ helpTextSource }) {
  const [, meta] = useField('verbosity');
  const isValid = !(meta.touched && meta.error);

  return (
    <VerbositySelectField
      fieldId="prompt-verbosity"
      tooltip={helpTextSource.verbosity}
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

function LabelsField({ helpTextSource }) {
  const [field, meta, helpers] = useField('labels');

  return (
    <FormGroup
      fieldId="prompt-labels"
      label={t`Labels`}
      labelIcon={<Popover content={helpTextSource.labels} />}
      validated={!meta.touched || !meta.error ? 'default' : 'error'}
      helperTextInvalid={meta.error}
    >
      <LabelSelect
        value={field.value}
        onChange={(labels) => helpers.setValue(labels)}
        createText={t`Create`}
        onError={(err) => helpers.setError(err)}
      />
    </FormGroup>
  );
}

export default OtherPromptsStep;
