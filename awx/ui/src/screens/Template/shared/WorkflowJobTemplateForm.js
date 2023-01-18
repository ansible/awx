import React, { useCallback, useEffect, useState } from 'react';
import { t } from '@lingui/macro';
import PropTypes, { shape } from 'prop-types';
import { useField, useFormikContext, withFormik } from 'formik';
import {
  Form,
  FormGroup,
  Checkbox,
  TextInput,
  Title,
} from '@patternfly/react-core';
import { required } from 'util/validators';
import FieldWithPrompt from 'components/FieldWithPrompt';
import FormField, { FormSubmitError } from 'components/FormField';
import {
  FormColumnLayout,
  FormFullWidthLayout,
  FormCheckboxLayout,
  SubFormLayout,
} from 'components/FormLayout';
import OrganizationLookup from 'components/Lookup/OrganizationLookup';
import { InventoryLookup } from 'components/Lookup';
import { VariablesField } from 'components/CodeEditor';
import FormActionGroup from 'components/FormActionGroup';
import ContentError from 'components/ContentError';
import CheckboxField from 'components/FormField/CheckboxField';
import Popover from 'components/Popover';
import { WorkFlowJobTemplate } from 'types';
import LabelSelect from 'components/LabelSelect';
import { TagMultiSelect } from 'components/MultiSelect';
import WebhookSubForm from './WebhookSubForm';
import getHelpText from './WorkflowJobTemplate.helptext';

const urlOrigin = window.location.origin;

function WorkflowJobTemplateForm({
  template,
  handleSubmit,
  handleCancel,
  submitError,
  isOrgAdmin,
  isInventoryDisabled,
}) {
  const helpText = getHelpText();
  const { setFieldValue, setFieldTouched } = useFormikContext();
  const [enableWebhooks, setEnableWebhooks] = useState(
    Boolean(template.webhook_service)
  );
  const [hasContentError, setContentError] = useState(null);
  const [askInventoryOnLaunchField] = useField('ask_inventory_on_launch');
  const [inventoryField, inventoryMeta, inventoryHelpers] =
    useField('inventory');
  const [labelsField, , labelsHelpers] = useField('labels');
  const [limitField, limitMeta, limitHelpers] = useField('limit');
  const [organizationField, organizationMeta, organizationHelpers] =
    useField('organization');
  const [scmField, , scmHelpers] = useField('scm_branch');
  const [, webhookServiceMeta, webhookServiceHelpers] =
    useField('webhook_service');
  const [, webhookUrlMeta, webhookUrlHelpers] = useField('webhook_url');
  const [, webhookKeyMeta, webhookKeyHelpers] = useField('webhook_key');
  const [, webhookCredentialMeta, webhookCredentialHelpers] =
    useField('webhook_credential');
  const [skipTagsField, , skipTagsHelpers] = useField('skip_tags');
  const [jobTagsField, , jobTagsHelpers] = useField('job_tags');

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

  const handleOrganizationChange = useCallback(
    (value) => {
      setFieldValue('organization', value);
      setFieldTouched('organization', true, false);
    },
    [setFieldValue, setFieldTouched]
  );

  const handleInventoryUpdate = useCallback(
    (value) => {
      setFieldValue('inventory', value);
      setFieldTouched('inventory', true, false);
    },
    [setFieldValue, setFieldTouched]
  );

  if (hasContentError) {
    return <ContentError error={hasContentError} />;
  }

  return (
    <Form autoComplete="off" onSubmit={handleSubmit}>
      <FormColumnLayout>
        <FormField
          id="wfjt-name"
          name="name"
          type="text"
          label={t`Name`}
          validate={required(null)}
          isRequired
        />
        <FormField
          id="wfjt-description"
          name="description"
          type="text"
          label={t`Description`}
        />
        <OrganizationLookup
          helperTextInvalid={organizationMeta.error}
          isValid={!organizationMeta.touched || !organizationMeta.error}
          onBlur={() => organizationHelpers.setTouched()}
          onChange={handleOrganizationChange}
          value={organizationField.value}
          touched={organizationMeta.touched}
          error={organizationMeta.error}
          required={isOrgAdmin}
          autoPopulate={isOrgAdmin}
          validate={
            isOrgAdmin ? required(t`Select a value for this field`) : undefined
          }
        />
        <FormGroup
          fieldId="inventory-lookup"
          validated={
            !(inventoryMeta.touched || askInventoryOnLaunchField.value) ||
            !inventoryMeta.error
              ? 'default'
              : 'error'
          }
          helperTextInvalid={inventoryMeta.error}
        >
          <InventoryLookup
            promptId="wfjt-ask-inventory-on-launch"
            promptName="ask_inventory_on_launch"
            tooltip={helpText.inventory}
            fieldId="wfjt-inventory"
            isPromptableField
            value={inventoryField.value}
            onBlur={() => inventoryHelpers.setTouched()}
            onChange={handleInventoryUpdate}
            touched={inventoryMeta.touched}
            error={inventoryMeta.error}
            isDisabled={isInventoryDisabled}
          />
        </FormGroup>
        <FieldWithPrompt
          fieldId="wfjt-limit"
          label={t`Limit`}
          promptId="template-ask-limit-on-launch"
          promptName="ask_limit_on_launch"
          tooltip={helpText.limit}
        >
          <TextInput
            id="wfjt-limit"
            value={limitField.value}
            validated={
              !limitMeta.touched || !limitMeta.error ? 'default' : 'error'
            }
            onChange={(value) => {
              limitHelpers.setValue(value);
            }}
          />
        </FieldWithPrompt>
        <FieldWithPrompt
          fieldId="wfjt-scm-branch"
          label={t`Source control branch`}
          promptId="wfjt-ask-scm-branch-on-launch"
          promptName="ask_scm_branch_on_launch"
          tooltip={helpText.sourceControlBranch}
        >
          <TextInput
            id="wfjt-scm-branch"
            value={scmField.value}
            onChange={(value) => {
              scmHelpers.setValue(value);
            }}
            aria-label={t`source control branch`}
          />
        </FieldWithPrompt>
      </FormColumnLayout>
      <FormFullWidthLayout>
        <FieldWithPrompt
          fieldId="template-labels"
          label={t`Labels`}
          promptId="template-ask-labels-on-launch"
          promptName="ask_labels_on_launch"
          tooltip={helpText.labels}
        >
          <LabelSelect
            value={labelsField.value}
            onChange={(labels) => labelsHelpers.setValue(labels)}
            onError={setContentError}
            createText={t`Create`}
          />
        </FieldWithPrompt>
      </FormFullWidthLayout>
      <FormFullWidthLayout>
        <VariablesField
          id="wfjt-variables"
          name="extra_vars"
          label={t`Variables`}
          promptId="template-ask-variables-on-launch"
          tooltip={helpText.variables}
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
      </FormFullWidthLayout>
      <FormGroup fieldId="options" label={t`Options`}>
        <FormCheckboxLayout isInline>
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
            name="allow_simultaneous"
            id="allow_simultaneous"
            tooltip={helpText.enableConcurrentJobs}
            label={t`Enable Concurrent Jobs`}
          />
        </FormCheckboxLayout>
      </FormGroup>

      {enableWebhooks && (
        <SubFormLayout>
          <Title size="md" headingLevel="h4">
            {t`Webhook details`}
          </Title>
          <WebhookSubForm templateType={template.type} />
        </SubFormLayout>
      )}

      {submitError && <FormSubmitError error={submitError} />}
      <FormActionGroup onCancel={handleCancel} onSubmit={handleSubmit} />
    </Form>
  );
}

WorkflowJobTemplateForm.propTypes = {
  template: WorkFlowJobTemplate,
  handleSubmit: PropTypes.func.isRequired,
  handleCancel: PropTypes.func.isRequired,
  submitError: shape({}),
  isOrgAdmin: PropTypes.bool,
  isInventoryDisabled: PropTypes.bool,
};

WorkflowJobTemplateForm.defaultProps = {
  submitError: null,
  template: {
    name: '',
    description: '',
    inventory: undefined,
    project: undefined,
  },
  isOrgAdmin: false,
  isInventoryDisabled: false,
};

const FormikApp = withFormik({
  mapPropsToValues({ template = {} }) {
    return {
      name: template.name || '',
      description: template.description || '',
      inventory: template?.summary_fields?.inventory || null,
      organization: template?.summary_fields?.organization || null,
      labels: template.summary_fields?.labels?.results || [],
      extra_vars: template.extra_vars || '---',
      limit: template.limit || '',
      scm_branch: template.scm_branch || '',
      skip_tags: template.skip_tags || '',
      job_tags: template.job_tags || '',
      allow_simultaneous: template.allow_simultaneous || false,
      webhook_credential: template?.summary_fields?.webhook_credential || null,
      webhook_service: template.webhook_service || '',
      ask_labels_on_launch: template.ask_labels_on_launch || false,
      ask_limit_on_launch: template.ask_limit_on_launch || false,
      ask_inventory_on_launch: template.ask_inventory_on_launch || false,
      ask_variables_on_launch: template.ask_variables_on_launch || false,
      ask_scm_branch_on_launch: template.ask_scm_branch_on_launch || false,
      ask_skip_tags_on_launch: template.ask_skip_tags_on_launch || false,
      ask_tags_on_launch: template.ask_tags_on_launch || false,
      webhook_url: template?.related?.webhook_receiver
        ? `${urlOrigin}${template.related.webhook_receiver}`
        : '',
      webhook_key: template.webhook_key || '',
    };
  },
  handleSubmit: async (values, { props, setErrors }) => {
    try {
      await props.handleSubmit(values);
    } catch (errors) {
      setErrors(errors);
    }
  },
})(WorkflowJobTemplateForm);

export { WorkflowJobTemplateForm as _WorkflowJobTemplateForm };
export default FormikApp;
