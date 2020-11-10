import React, { useCallback, useEffect, useState } from 'react';
import { t } from '@lingui/macro';
import PropTypes, { shape } from 'prop-types';

import { withI18n } from '@lingui/react';
import { useField, useFormikContext, withFormik } from 'formik';
import {
  Form,
  FormGroup,
  Checkbox,
  TextInput,
  Title,
} from '@patternfly/react-core';
import { required } from '../../../util/validators';

import FieldWithPrompt from '../../../components/FieldWithPrompt';
import FormField, { FormSubmitError } from '../../../components/FormField';
import {
  FormColumnLayout,
  FormFullWidthLayout,
  FormCheckboxLayout,
  SubFormLayout,
} from '../../../components/FormLayout';
import OrganizationLookup from '../../../components/Lookup/OrganizationLookup';
import { InventoryLookup } from '../../../components/Lookup';
import { VariablesField } from '../../../components/CodeMirrorInput';
import FormActionGroup from '../../../components/FormActionGroup';
import ContentError from '../../../components/ContentError';
import CheckboxField from '../../../components/FormField/CheckboxField';
import Popover from '../../../components/Popover';
import LabelSelect from './LabelSelect';
import WebhookSubForm from './WebhookSubForm';
import { WorkFlowJobTemplate } from '../../../types';

const urlOrigin = window.location.origin;

function WorkflowJobTemplateForm({
  template,
  handleSubmit,
  handleCancel,
  i18n,
  submitError,
}) {
  const { setFieldValue } = useFormikContext();
  const [enableWebhooks, setEnableWebhooks] = useState(
    Boolean(template.webhook_service)
  );
  const [hasContentError, setContentError] = useState(null);
  const [askInventoryOnLaunchField] = useField('ask_inventory_on_launch');
  const [inventoryField, inventoryMeta, inventoryHelpers] = useField(
    'inventory'
  );
  const [labelsField, , labelsHelpers] = useField('labels');
  const [limitField, limitMeta, limitHelpers] = useField('limit');
  const [organizationField, organizationMeta] = useField('organization');
  const [scmField, , scmHelpers] = useField('scm_branch');
  const [, webhookServiceMeta, webhookServiceHelpers] = useField(
    'webhook_service'
  );
  const [, webhookUrlMeta, webhookUrlHelpers] = useField('webhook_url');
  const [, webhookKeyMeta, webhookKeyHelpers] = useField('webhook_key');
  const [, webhookCredentialMeta, webhookCredentialHelpers] = useField(
    'webhook_credential'
  );

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

  const onOrganizationChange = useCallback(
    value => {
      setFieldValue('organization', value);
    },
    [setFieldValue]
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
          label={i18n._(t`Name`)}
          validate={required(null, i18n)}
          isRequired
        />
        <FormField
          id="wfjt-description"
          name="description"
          type="text"
          label={i18n._(t`Description`)}
        />
        <OrganizationLookup
          helperTextInvalid={organizationMeta.error}
          onChange={onOrganizationChange}
          value={organizationField.value}
          isValid={!organizationMeta.error}
        />
        <>
          <InventoryLookup
            promptId="wfjt-ask-inventory-on-launch"
            promptName="ask_inventory_on_launch"
            tooltip={i18n._(
              t`Select an inventory for the workflow. This inventory is applied to all job template nodes that prompt for an inventory.`
            )}
            fieldId="wfjt-inventory"
            isPromptableField
            value={inventoryField.value}
            onBlur={() => inventoryHelpers.setTouched()}
            onChange={value => {
              inventoryHelpers.setValue(value);
            }}
            required={!askInventoryOnLaunchField.value}
            touched={inventoryMeta.touched}
            error={inventoryMeta.error}
          />
          {(inventoryMeta.touched || askInventoryOnLaunchField.value) &&
            inventoryMeta.error && (
              <div
                className="pf-c-form__helper-text pf-m-error"
                aria-live="polite"
              >
                {inventoryMeta.error}
              </div>
            )}
        </>
        <FieldWithPrompt
          fieldId="wjft-limit"
          label={i18n._(t`Limit`)}
          promptId="template-ask-limit-on-launch"
          promptName="ask_limit_on_launch"
          tooltip={i18n._(t`Provide a host pattern to further constrain
                  the list of hosts that will be managed or affected by the
                  playbook. Multiple patterns are allowed. Refer to Ansible
                  documentation for more information and examples on patterns.`)}
        >
          <TextInput
            id="text-wfjt-limit"
            {...limitField}
            validated={
              !limitMeta.touched || !limitMeta.error ? 'default' : 'error'
            }
            onChange={value => {
              limitHelpers.setValue(value);
            }}
          />
        </FieldWithPrompt>

        <FieldWithPrompt
          fieldId="wfjt-scm-branch"
          label={i18n._(t`Source control branch`)}
          promptId="wfjt-ask-scm-branch-on-launch"
          promptName="ask_scm_branch_on_launch"
          tooltip={i18n._(
            t`Select a branch for the workflow. This branch is applied to all job template nodes that prompt for a branch.`
          )}
        >
          <TextInput
            id="text-wfjt-scm-branch"
            {...scmField}
            onChange={value => {
              scmHelpers.setValue(value);
            }}
          />
        </FieldWithPrompt>
      </FormColumnLayout>
      <FormFullWidthLayout>
        <FormGroup
          label={i18n._(t`Labels`)}
          labelIcon={
            <Popover
              content={i18n._(t`Optional labels that describe this job template,
                    such as 'dev' or 'test'. Labels can be used to group and filter
                    job templates and completed jobs.`)}
            />
          }
          fieldId="template-labels"
        >
          <LabelSelect
            value={labelsField.value}
            onChange={labels => labelsHelpers.setValue(labels)}
            onError={setContentError}
            createText={i18n._(t`Create`)}
          />
        </FormGroup>
      </FormFullWidthLayout>
      <FormFullWidthLayout>
        <VariablesField
          id="wfjt-variables"
          name="extra_vars"
          label={i18n._(t`Variables`)}
          promptId="template-ask-variables-on-launch"
          tooltip={i18n._(
            t`Pass extra command line variables to the playbook. This is the -e or --extra-vars command line parameter for ansible-playbook. Provide key/value pairs using either YAML or JSON. Refer to the Ansible Tower documentation for example syntax.`
          )}
        />
      </FormFullWidthLayout>
      <FormGroup fieldId="options" label={i18n._(t`Options`)}>
        <FormCheckboxLayout isInline>
          <Checkbox
            aria-label={i18n._(t`Enable Webhook`)}
            label={
              <span>
                {i18n._(t`Enable Webhook`)}
                &nbsp;
                <Popover
                  content={i18n._(
                    t`Enable Webhook for this workflow job template.`
                  )}
                />
              </span>
            }
            id="wfjt-enabled-webhooks"
            isChecked={enableWebhooks}
            onChange={checked => {
              setEnableWebhooks(checked);
            }}
          />
          <CheckboxField
            name="allow_simultaneous"
            id="allow_simultaneous"
            tooltip={i18n._(
              t`If enabled, simultaneous runs of this workflow job template will be allowed.`
            )}
            label={i18n._(t`Enable Concurrent Jobs`)}
          />
        </FormCheckboxLayout>
      </FormGroup>

      {enableWebhooks && (
        <SubFormLayout>
          <Title size="md" headingLevel="h4">
            {i18n._(t`Webhook details`)}
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
};

WorkflowJobTemplateForm.defaultProps = {
  submitError: null,
  template: {
    name: '',
    description: '',
    inventory: undefined,
    project: undefined,
  },
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
export default withI18n()(FormikApp);
