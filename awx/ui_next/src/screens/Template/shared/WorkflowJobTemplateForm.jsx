import React, { useState } from 'react';
import { t } from '@lingui/macro';

import PropTypes, { shape } from 'prop-types';

import { withI18n } from '@lingui/react';
import { useField, withFormik } from 'formik';
import { Form, FormGroup, Checkbox } from '@patternfly/react-core';
import { required } from '../../../util/validators';

import FormField, {
  FieldTooltip,
  FormSubmitError,
} from '../../../components/FormField';
import {
  FormColumnLayout,
  FormFullWidthLayout,
  FormCheckboxLayout,
} from '../../../components/FormLayout';
import OrganizationLookup from '../../../components/Lookup/OrganizationLookup';
import { InventoryLookup } from '../../../components/Lookup';
import { VariablesField } from '../../../components/CodeMirrorInput';
import FormActionGroup from '../../../components/FormActionGroup';
import ContentError from '../../../components/ContentError';
import CheckboxField from '../../../components/FormField/CheckboxField';
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
  const [hasContentError, setContentError] = useState(null);

  const [organizationField, organizationMeta, organizationHelpers] = useField(
    'organization'
  );
  const [inventoryField, inventoryMeta, inventoryHelpers] = useField(
    'inventory'
  );
  const [labelsField, , labelsHelpers] = useField('labels');

  const [enableWebhooks, setEnableWebhooks] = useState(
    Boolean(template.webhook_service)
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
          onChange={value => {
            organizationHelpers.setValue(value || null);
          }}
          value={organizationField.value}
          isValid={!organizationMeta.error}
        />
        <FormGroup label={i18n._(t`Inventory`)} fieldId="wfjt-inventory">
          <FieldTooltip
            content={i18n._(
              t`Select an inventory for the workflow. This inventory is applied to all job template nodes that prompt for an inventory.`
            )}
          />
          <InventoryLookup
            value={inventoryField.value}
            isValid={!inventoryMeta.error}
            helperTextInvalid={inventoryMeta.error}
            onChange={value => {
              inventoryHelpers.setValue(value || null);
            }}
          />
        </FormGroup>
        <FormField
          type="text"
          name="limit"
          id="wfjt-limit"
          label={i18n._(t`Limit`)}
          tooltip={i18n._(
            t`Provide a host pattern to further constrain the list of hosts that will be managed or affected by the workflow. This limit is applied to all job template nodes that prompt for a limit. Refer to Ansible documentation for more information and examples on patterns.`
          )}
        />
        <FormField
          type="text"
          label={i18n._(t`Source Control Branch`)}
          tooltip={i18n._(
            t`Select a branch for the workflow. This branch is applied to all job template nodes that prompt for a branch.`
          )}
          id="wfjt-scm_branch"
          name="scm_branch"
        />
      </FormColumnLayout>
      <FormFullWidthLayout>
        <FormGroup label={i18n._(t`Labels`)} fieldId="template-labels">
          <FieldTooltip
            content={i18n._(t`Optional labels that describe this job template,
                    such as 'dev' or 'test'. Labels can be used to group and filter
                    job templates and completed jobs.`)}
          />
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
          tooltip={i18n._(
            t`Pass extra command line variables to the playbook. This is the -e or --extra-vars command line parameter for ansible-playbook. Provide key/value pairs using either YAML or JSON. Refer to the Ansible Tower documentation for example syntax.`
          )}
        />
      </FormFullWidthLayout>
      <FormCheckboxLayout fieldId="options" isInline label={i18n._(t`Options`)}>
        <Checkbox
          aria-label={i18n._(t`Enable Webhook`)}
          label={
            <span>
              {i18n._(t`Enable Webhook`)}
              &nbsp;
              <FieldTooltip
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
      <WebhookSubForm
        enableWebhooks={enableWebhooks}
        templateType={template.type}
      />
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
