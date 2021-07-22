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
import LabelSelect from './LabelSelect';
import WebhookSubForm from './WebhookSubForm';

const urlOrigin = window.location.origin;

function WorkflowJobTemplateForm({
  template,
  handleSubmit,
  handleCancel,
  submitError,
  isOrgAdmin,
}) {
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
            tooltip={t`Select an inventory for the workflow. This inventory is applied to all workflow nodes that prompt for an inventory.`}
            fieldId="wfjt-inventory"
            isPromptableField
            value={inventoryField.value}
            onBlur={() => inventoryHelpers.setTouched()}
            onChange={handleInventoryUpdate}
            touched={inventoryMeta.touched}
            error={inventoryMeta.error}
          />
        </FormGroup>
        <FieldWithPrompt
          fieldId="wfjt-limit"
          label={t`Limit`}
          promptId="template-ask-limit-on-launch"
          promptName="ask_limit_on_launch"
          tooltip={t`Provide a host pattern to further constrain
                  the list of hosts that will be managed or affected by the
                  playbook. Multiple patterns are allowed. Refer to Ansible
                  documentation for more information and examples on patterns.`}
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
          tooltip={t`Select a branch for the workflow. This branch is applied to all job template nodes that prompt for a branch.`}
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
        <FormGroup
          label={t`Labels`}
          labelIcon={
            <Popover
              content={t`Optional labels that describe this job template,
                    such as 'dev' or 'test'. Labels can be used to group and filter
                    job templates and completed jobs.`}
            />
          }
          fieldId="template-labels"
        >
          <LabelSelect
            value={labelsField.value}
            onChange={(labels) => labelsHelpers.setValue(labels)}
            onError={setContentError}
            createText={t`Create`}
          />
        </FormGroup>
      </FormFullWidthLayout>
      <FormFullWidthLayout>
        <VariablesField
          id="wfjt-variables"
          name="extra_vars"
          label={t`Variables`}
          promptId="template-ask-variables-on-launch"
          tooltip={t`Pass extra command line variables to the playbook. This is the -e or --extra-vars command line parameter for ansible-playbook. Provide key/value pairs using either YAML or JSON. Refer to the Ansible Tower documentation for example syntax.`}
        />
      </FormFullWidthLayout>
      <FormGroup fieldId="options" label={t`Options`}>
        <FormCheckboxLayout isInline>
          <Checkbox
            aria-label={t`Enable Webhook`}
            label={
              <span>
                {t`Enable Webhook`}
                &nbsp;
                <Popover
                  content={t`Enable Webhook for this workflow job template.`}
                />
              </span>
            }
            id="wfjt-enabled-webhooks"
            isChecked={enableWebhooks}
            onChange={(checked) => {
              setEnableWebhooks(checked);
            }}
          />
          <CheckboxField
            name="allow_simultaneous"
            id="allow_simultaneous"
            tooltip={t`If enabled, simultaneous runs of this workflow job template will be allowed.`}
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
      allow_simultaneous: template.allow_simultaneous || false,
      webhook_credential: template?.summary_fields?.webhook_credential || null,
      webhook_service: template.webhook_service || '',
      ask_limit_on_launch: template.ask_limit_on_launch || false,
      ask_inventory_on_launch: template.ask_inventory_on_launch || false,
      ask_variables_on_launch: template.ask_variables_on_launch || false,
      ask_scm_branch_on_launch: template.ask_scm_branch_on_launch || false,
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
