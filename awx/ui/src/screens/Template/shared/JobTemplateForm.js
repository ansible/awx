import React, { useState, useEffect, useCallback } from 'react';
import PropTypes from 'prop-types';

import { t } from '@lingui/macro';
import { withFormik, useField } from 'formik';
import {
  Form,
  FormGroup,
  Switch,
  Checkbox,
  TextInput,
  Title,
} from '@patternfly/react-core';
import ContentError from 'components/ContentError';
import ContentLoading from 'components/ContentLoading';
import AnsibleSelect from 'components/AnsibleSelect';
import { TagMultiSelect } from 'components/MultiSelect';
import useRequest from 'hooks/useRequest';
import useBrandName from 'hooks/useBrandName';
import FormActionGroup from 'components/FormActionGroup';
import FormField, {
  CheckboxField,
  FormSubmitError,
} from 'components/FormField';
import FieldWithPrompt from 'components/FieldWithPrompt';
import {
  FormColumnLayout,
  FormFullWidthLayout,
  FormCheckboxLayout,
  SubFormLayout,
} from 'components/FormLayout';
import { VariablesField } from 'components/CodeEditor';
import { required, combine, maxLength } from 'util/validators';
import { JobTemplate } from 'types';
import {
  InventoryLookup,
  InstanceGroupsLookup,
  ProjectLookup,
  MultiCredentialsLookup,
  ExecutionEnvironmentLookup,
} from 'components/Lookup';
import Popover from 'components/Popover';
import { JobTemplatesAPI } from 'api';
import useIsMounted from 'hooks/useIsMounted';
import LabelSelect from 'components/LabelSelect';
import { VerbositySelectField } from 'components/VerbositySelectField';
import PlaybookSelect from './PlaybookSelect';
import WebhookSubForm from './WebhookSubForm';
import getHelpText from './JobTemplate.helptext';

const { origin } = document.location;

function JobTemplateForm({
  template,
  handleCancel,
  handleSubmit,
  setFieldValue,
  setFieldTouched,
  submitError,
  validateField,
  isOverrideDisabledLookup, // TODO: this is a confusing variable name
}) {
  const helpText = getHelpText();
  const [contentError, setContentError] = useState(false);
  const [allowCallbacks, setAllowCallbacks] = useState(
    Boolean(template?.host_config_key)
  );
  const [enableWebhooks, setEnableWebhooks] = useState(
    Boolean(template?.webhook_service)
  );
  const isMounted = useIsMounted();
  const brandName = useBrandName();

  const [askInventoryOnLaunchField] = useField('ask_inventory_on_launch');
  const [jobTypeField, jobTypeMeta, jobTypeHelpers] = useField({
    name: 'job_type',
    validate: required(null),
  });
  const [inventoryField, inventoryMeta, inventoryHelpers] =
    useField('inventory');
  const [projectField, projectMeta, projectHelpers] = useField('project');
  const [scmField, , scmHelpers] = useField('scm_branch');
  const [playbookField, playbookMeta, playbookHelpers] = useField({
    name: 'playbook',
    validate: required(null),
  });
  const [credentialField, , credentialHelpers] = useField('credentials');
  const [labelsField, , labelsHelpers] = useField('labels');
  const [limitField, limitMeta, limitHelpers] = useField('limit');
  const [diffModeField, , diffModeHelpers] = useField('diff_mode');
  const [instanceGroupsField, , instanceGroupsHelpers] =
    useField('instanceGroups');
  const [jobTagsField, , jobTagsHelpers] = useField('job_tags');
  const [skipTagsField, , skipTagsHelpers] = useField('skip_tags');

  const [, webhookServiceMeta, webhookServiceHelpers] =
    useField('webhook_service');
  const [, webhookUrlMeta, webhookUrlHelpers] = useField('webhook_url');
  const [, webhookKeyMeta, webhookKeyHelpers] = useField('webhook_key');
  const [, webhookCredentialMeta, webhookCredentialHelpers] =
    useField('webhook_credential');

  const [
    executionEnvironmentField,
    executionEnvironmentMeta,
    executionEnvironmentHelpers,
  ] = useField('execution_environment');

  const {
    request: loadRelatedInstanceGroups,
    error: instanceGroupError,
    isLoading: instanceGroupLoading,
  } = useRequest(
    useCallback(async () => {
      if (!template?.id) {
        return;
      }
      const { data } = await JobTemplatesAPI.readInstanceGroups(template.id);
      if (isMounted.current) {
        setFieldValue('initialInstanceGroups', data.results);
        setFieldValue('instanceGroups', [...data.results]);
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [setFieldValue, template]),
    {
      isLoading: true,
    }
  );

  useEffect(() => {
    loadRelatedInstanceGroups();
  }, [loadRelatedInstanceGroups]);

  useEffect(() => {
    if (enableWebhooks) {
      webhookServiceHelpers.setValue(webhookServiceMeta.initialValue);
      webhookUrlHelpers.setValue(webhookUrlMeta.initialValue);
      webhookKeyHelpers.setValue(webhookKeyMeta.initialValue);
      webhookCredentialHelpers.setValue(webhookCredentialMeta.initialValue);
    } else {
      webhookServiceHelpers.setValue('');
      webhookUrlHelpers.setValue('');
      webhookKeyHelpers.setValue('');
      webhookCredentialHelpers.setValue(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enableWebhooks]);

  const handleProjectValidation = (project) => {
    if (!project) {
      return t`This field must not be blank`;
    }
    if (project?.status === 'never updated') {
      return t`This Project needs to be updated`;
    }
    return undefined;
  };

  const handleProjectUpdate = useCallback(
    (value) => {
      setFieldValue('project', value);
      setFieldValue('playbook', '', false);
      setFieldValue('scm_branch', '', false);
      setFieldTouched('project', true, false);
    },
    [setFieldValue, setFieldTouched]
  );

  const handleInventoryValidation = (inventory) => {
    if (!inventory && !askInventoryOnLaunchField.value) {
      return t`Please select an Inventory or check the Prompt on Launch option`;
    }
    return undefined;
  };

  const handleInventoryUpdate = useCallback(
    (value) => {
      setFieldValue('inventory', value);
      setFieldTouched('inventory', true, false);
    },
    [setFieldValue, setFieldTouched]
  );

  const handleExecutionEnvironmentUpdate = useCallback(
    (value) => {
      setFieldValue('execution_environment', value);
      setFieldTouched('execution_environment', true, false);
    },
    [setFieldValue, setFieldTouched]
  );

  const handlePlaybookUpdate = useCallback(
    (value) => {
      setFieldValue('playbook', value);
      setFieldTouched('playbook', true, false);
    },
    [setFieldValue, setFieldTouched]
  );

  useEffect(() => {
    validateField('inventory');
  }, [askInventoryOnLaunchField.value, validateField]);

  const jobTypeOptions = [
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
  let callbackUrl;
  if (template?.related) {
    const path = template.related.callback || `${template.url}callback`;
    callbackUrl = `${origin}${path}`;
  }

  if (instanceGroupLoading) {
    return <ContentLoading />;
  }

  if (contentError || instanceGroupError) {
    return <ContentError error={contentError || instanceGroupError} />;
  }

  return (
    <Form autoComplete="off" onSubmit={handleSubmit}>
      <FormColumnLayout>
        <FormField
          id="template-name"
          name="name"
          type="text"
          label={t`Name`}
          validate={combine([required(null), maxLength(512)])}
          isRequired
        />
        <FormField
          id="template-description"
          name="description"
          type="text"
          label={t`Description`}
        />
        <FieldWithPrompt
          fieldId="template-job-type"
          isRequired
          label={t`Job Type`}
          promptId="template-ask-job-type-on-launch"
          promptName="ask_job_type_on_launch"
          tooltip={helpText.jobType}
        >
          <AnsibleSelect
            {...jobTypeField}
            isValid={!jobTypeMeta.touched || !jobTypeMeta.error}
            id="template-job-type"
            data={jobTypeOptions}
            onChange={(event, value) => {
              jobTypeHelpers.setValue(value);
            }}
          />
        </FieldWithPrompt>
        <FormGroup
          fieldId="template-inventory"
          validated={
            !(inventoryMeta.touched || askInventoryOnLaunchField.value) ||
            !inventoryMeta.error
              ? 'default'
              : 'error'
          }
          helperTextInvalid={inventoryMeta.error}
          isRequired={!askInventoryOnLaunchField.value}
        >
          <InventoryLookup
            fieldId="template-inventory"
            value={inventoryField.value}
            promptId="template-ask-inventory-on-launch"
            promptName="ask_inventory_on_launch"
            isPromptableField
            tooltip={helpText.inventory}
            onBlur={() => inventoryHelpers.setTouched()}
            onChange={handleInventoryUpdate}
            required={!askInventoryOnLaunchField.value}
            touched={inventoryMeta.touched}
            error={inventoryMeta.error}
            isOverrideDisabled={isOverrideDisabledLookup}
            validate={handleInventoryValidation}
          />
        </FormGroup>

        <ProjectLookup
          value={projectField.value}
          onBlur={() => projectHelpers.setTouched()}
          tooltip={helpText.project}
          isValid={Boolean(
            !projectMeta.touched || (!projectMeta.error && projectField.value)
          )}
          helperTextInvalid={projectMeta.error}
          onChange={handleProjectUpdate}
          required
          autoPopulate={!template?.id}
          isOverrideDisabled={isOverrideDisabledLookup}
          validate={handleProjectValidation}
        />

        <ExecutionEnvironmentLookup
          helperTextInvalid={executionEnvironmentMeta.error}
          isValid={
            !executionEnvironmentMeta.touched || !executionEnvironmentMeta.error
          }
          onBlur={() => executionEnvironmentHelpers.setTouched()}
          value={executionEnvironmentField.value}
          onChange={handleExecutionEnvironmentUpdate}
          popoverContent={helpText.executionEnvironmentForm}
          tooltip={t`Select a project before editing the execution environment.`}
          globallyAvailable
          isDisabled={!projectField.value?.id}
          projectId={projectField.value?.id}
        />

        {projectField.value?.allow_override && (
          <FieldWithPrompt
            fieldId="template-scm-branch"
            label={t`Source Control Branch`}
            promptId="template-ask-scm-branch-on-launch"
            promptName="ask_scm_branch_on_launch"
            tooltip={helpText.sourceControlBranch}
          >
            <TextInput
              id="template-scm-branch"
              onChange={(value) => {
                scmHelpers.setValue(value);
              }}
              value={scmField.value}
              aria-label={t`source control branch`}
            />
          </FieldWithPrompt>
        )}
        <FormGroup
          fieldId="template-playbook"
          helperTextInvalid={playbookMeta.error}
          validated={
            !playbookMeta.touched || !playbookMeta.error ? 'default' : 'error'
          }
          isRequired
          label={t`Playbook`}
          labelIcon={<Popover content={helpText.playbook} />}
        >
          <PlaybookSelect
            onChange={handlePlaybookUpdate}
            projectId={projectField.value?.id}
            isValid={!playbookMeta.touched || !playbookMeta.error}
            selected={playbookField.value}
            onBlur={() => playbookHelpers.setTouched()}
            onError={setContentError}
          />
        </FormGroup>
        <FormFullWidthLayout>
          <FieldWithPrompt
            fieldId="template-credentials"
            label={t`Credentials`}
            promptId="template-ask-credential-on-launch"
            promptName="ask_credential_on_launch"
            tooltip={helpText.credentials}
          >
            <MultiCredentialsLookup
              value={credentialField.value}
              onChange={(newCredentials) =>
                credentialHelpers.setValue(newCredentials)
              }
              onError={setContentError}
            />
          </FieldWithPrompt>
          <FormGroup
            label={t`Labels`}
            labelIcon={<Popover content={helpText.labels} />}
            fieldId="template-labels"
          >
            <LabelSelect
              value={labelsField.value}
              onChange={(labels) => labelsHelpers.setValue(labels)}
              onError={setContentError}
              createText={t`Create`}
            />
          </FormGroup>
          <VariablesField
            id="template-variables"
            name="extra_vars"
            label={t`Variables`}
            promptId="template-ask-variables-on-launch"
            tooltip={helpText.variables}
          />
          <FormColumnLayout>
            <FormField
              id="template-forks"
              name="forks"
              type="number"
              min="0"
              label={t`Forks`}
              tooltip={helpText.forks}
            />
            <FieldWithPrompt
              fieldId="template-limit"
              label={t`Limit`}
              promptId="template-ask-limit-on-launch"
              promptName="ask_limit_on_launch"
              tooltip={helpText.limit}
            >
              <TextInput
                id="template-limit"
                {...limitField}
                validated={
                  !limitMeta.touched || !limitMeta.error ? 'default' : 'error'
                }
                onChange={(value) => {
                  limitHelpers.setValue(value);
                }}
              />
            </FieldWithPrompt>
            <VerbositySelectField
              fieldId="template-verbosity"
              promptId="template-ask-verbosity-on-launch"
              promptName="ask_verbosity_on_launch"
              tooltip={helpText.verbosity}
            />
            <FormField
              id="template-job-slicing"
              name="job_slice_count"
              type="number"
              min="1"
              label={t`Job Slicing`}
              tooltip={helpText.jobSlicing}
            />
            <FormField
              id="template-timeout"
              name="timeout"
              type="number"
              min="0"
              label={t`Timeout`}
              tooltip={helpText.timeout}
            />
            <FieldWithPrompt
              fieldId="template-diff-mode"
              label={t`Show Changes`}
              promptId="template-ask-diff-mode-on-launch"
              promptName="ask_diff_mode_on_launch"
              tooltip={helpText.showChanges}
            >
              <Switch
                id="template-show-changes"
                label={diffModeField.value ? t`On` : t`Off`}
                isChecked={diffModeField.value}
                onChange={(checked) => diffModeHelpers.setValue(checked)}
              />
            </FieldWithPrompt>
            <FormFullWidthLayout>
              <InstanceGroupsLookup
                value={instanceGroupsField.value}
                onChange={(value) => instanceGroupsHelpers.setValue(value)}
                tooltip={helpText.instanceGroups}
                fieldName="instanceGroups"
              />
              <FieldWithPrompt
                fieldId="template-tags"
                label={t`Job Tags`}
                promptId="template-ask-tags-on-launch"
                promptName="ask_tags_on_launch"
                tooltip={helpText.jobTags}
              >
                <TagMultiSelect
                  value={jobTagsField.value}
                  onChange={(value) => jobTagsHelpers.setValue(value)}
                />
              </FieldWithPrompt>
              <FieldWithPrompt
                fieldId="template-skip-tags"
                label={t`Skip Tags`}
                promptId="template-ask-skip-tags-on-launch"
                promptName="ask_skip_tags_on_launch"
                tooltip={helpText.skipTags}
              >
                <TagMultiSelect
                  value={skipTagsField.value}
                  onChange={(value) => skipTagsHelpers.setValue(value)}
                />
              </FieldWithPrompt>
              <FormGroup
                fieldId="template-option-checkboxes"
                label={t`Options`}
              >
                <FormCheckboxLayout>
                  <CheckboxField
                    id="option-privilege-escalation"
                    name="become_enabled"
                    label={t`Privilege Escalation`}
                    tooltip={helpText.privilegeEscalation}
                  />
                  <Checkbox
                    aria-label={t`Provisioning Callbacks`}
                    label={
                      <span>
                        {t`Provisioning Callbacks`}
                        &nbsp;
                        <Popover
                          content={helpText.provisioningCallbacks(brandName)}
                        />
                      </span>
                    }
                    id="option-callbacks"
                    ouiaId="option-callbacks"
                    isChecked={allowCallbacks}
                    onChange={(checked) => {
                      setAllowCallbacks(checked);
                    }}
                  />
                  <Checkbox
                    aria-label={t`Enable Webhook`}
                    label={
                      <span>
                        {t`Enable Webhook`}
                        &nbsp;
                        <Popover content={helpText.enableWebhook} />
                      </span>
                    }
                    id="wfjt-enabled-webhooks"
                    ouiaId="wfjt-enabled-webhooks"
                    isChecked={enableWebhooks}
                    onChange={(checked) => {
                      setEnableWebhooks(checked);
                    }}
                  />
                  <CheckboxField
                    id="option-concurrent"
                    name="allow_simultaneous"
                    label={t`Concurrent Jobs`}
                    tooltip={helpText.concurrentJobs}
                  />
                  <CheckboxField
                    id="option-fact-cache"
                    name="use_fact_cache"
                    label={t`Enable Fact Storage`}
                    tooltip={helpText.enableFactStorage}
                  />
                </FormCheckboxLayout>
              </FormGroup>
            </FormFullWidthLayout>

            {(allowCallbacks || enableWebhooks) && (
              <SubFormLayout>
                {allowCallbacks && (
                  <>
                    <Title size="md" headingLevel="h4">
                      {t`Provisioning Callback details`}
                    </Title>
                    <FormColumnLayout>
                      {callbackUrl && (
                        <FormGroup
                          label={t`Provisioning Callback URL`}
                          fieldId="template-callback-url"
                        >
                          <TextInput
                            id="template-callback-url"
                            isDisabled
                            value={callbackUrl}
                          />
                        </FormGroup>
                      )}
                      <FormField
                        id="template-host-config-key"
                        name="host_config_key"
                        label={t`Host Config Key`}
                        validate={allowCallbacks ? required(null) : null}
                        isRequired={allowCallbacks}
                      />
                    </FormColumnLayout>
                  </>
                )}

                {allowCallbacks && enableWebhooks && <br />}

                {enableWebhooks && (
                  <>
                    <Title size="md" headingLevel="h4">
                      {t`Webhook details`}
                    </Title>
                    <FormColumnLayout>
                      <WebhookSubForm templateType={template.type} />
                    </FormColumnLayout>
                  </>
                )}
              </SubFormLayout>
            )}
          </FormColumnLayout>
        </FormFullWidthLayout>
        <FormSubmitError error={submitError} />
        <FormActionGroup onCancel={handleCancel} onSubmit={handleSubmit} />
      </FormColumnLayout>
    </Form>
  );
}
JobTemplateForm.propTypes = {
  template: JobTemplate,
  handleCancel: PropTypes.func.isRequired,
  handleSubmit: PropTypes.func.isRequired,
  submitError: PropTypes.shape({}),
  isOverrideDisabledLookup: PropTypes.bool,
};

JobTemplateForm.defaultProps = {
  template: {
    name: '',
    description: '',
    job_type: 'run',
    inventory: undefined,
    project: undefined,
    playbook: '',
    scm_branch: '',
    summary_fields: {
      inventory: null,
      labels: { results: [] },
      project: null,
      credentials: [],
    },
    isNew: true,
  },
  submitError: null,
  isOverrideDisabledLookup: false,
};

const FormikApp = withFormik({
  mapPropsToValues({ projectValues = {}, template = {} }) {
    const {
      summary_fields = {
        labels: { results: [] },
        inventory: null,
      },
    } = template;

    return {
      allow_callbacks: template.allow_callbacks || false,
      allow_simultaneous: template.allow_simultaneous || false,
      ask_credential_on_launch: template.ask_credential_on_launch || false,
      ask_diff_mode_on_launch: template.ask_diff_mode_on_launch || false,
      ask_inventory_on_launch: template.ask_inventory_on_launch || false,
      ask_job_type_on_launch: template.ask_job_type_on_launch || false,
      ask_limit_on_launch: template.ask_limit_on_launch || false,
      ask_scm_branch_on_launch: template.ask_scm_branch_on_launch || false,
      ask_skip_tags_on_launch: template.ask_skip_tags_on_launch || false,
      ask_tags_on_launch: template.ask_tags_on_launch || false,
      ask_variables_on_launch: template.ask_variables_on_launch || false,
      ask_verbosity_on_launch: template.ask_verbosity_on_launch || false,
      become_enabled: template.become_enabled || false,
      credentials: summary_fields.credentials || [],
      description: template.description || '',
      diff_mode: template.diff_mode || false,
      extra_vars: template.extra_vars || '---\n',
      forks: template.forks || 0,
      host_config_key: template.host_config_key || '',
      initialInstanceGroups: [],
      instanceGroups: [],
      inventory: summary_fields?.inventory || null,
      job_slice_count: template.job_slice_count || 1,
      job_tags: template.job_tags || '',
      job_type: template.job_type || 'run',
      labels: summary_fields.labels.results || [],
      limit: template.limit || '',
      name: template.name || '',
      playbook: template.playbook || '',
      project: summary_fields?.project || projectValues || null,
      scm_branch: template.scm_branch || '',
      skip_tags: template.skip_tags || '',
      timeout: template.timeout || 0,
      use_fact_cache: template.use_fact_cache || false,
      verbosity: template.verbosity || '0',
      webhook_service: template.webhook_service || '',
      webhook_url: template?.related?.webhook_receiver
        ? `${origin}${template.related.webhook_receiver}`
        : t`a new webhook url will be generated on save.`.toUpperCase(),
      webhook_key:
        template.webhook_key ||
        t`a new webhook key will be generated on save.`.toUpperCase(),
      webhook_credential: template?.summary_fields?.webhook_credential || null,
      execution_environment:
        template.summary_fields?.execution_environment || null,
    };
  },
  handleSubmit: async (values, { props, setErrors }) => {
    try {
      await props.handleSubmit(values);
    } catch (errors) {
      setErrors(errors);
    }
  },
})(JobTemplateForm);

export { JobTemplateForm as _JobTemplateForm };
export default FormikApp;
