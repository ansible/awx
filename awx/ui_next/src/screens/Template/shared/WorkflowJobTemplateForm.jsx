import React, { useState, useEffect, useCallback } from 'react';
import { t } from '@lingui/macro';
import { useRouteMatch, useParams, withRouter } from 'react-router-dom';

import PropTypes, { shape } from 'prop-types';

import { withI18n } from '@lingui/react';
import { useField, withFormik } from 'formik';
import {
  Form,
  FormGroup,
  InputGroup,
  Button,
  TextInput,
  Checkbox,
} from '@patternfly/react-core';
import { required } from '@util/validators';
import { SyncAltIcon } from '@patternfly/react-icons';

import AnsibleSelect from '@components/AnsibleSelect';
import { WorkflowJobTemplatesAPI, CredentialTypesAPI } from '@api';

import useRequest from '@util/useRequest';
import FormField, {
  FieldTooltip,
  FormSubmitError,
} from '@components/FormField';
import {
  FormColumnLayout,
  FormFullWidthLayout,
  FormCheckboxLayout,
} from '@components/FormLayout';
import ContentLoading from '@components/ContentLoading';
import OrganizationLookup from '@components/Lookup/OrganizationLookup';
import CredentialLookup from '@components/Lookup/CredentialLookup';
import { InventoryLookup } from '@components/Lookup';
import { VariablesField } from '@components/CodeMirrorInput';
import FormActionGroup from '@components/FormActionGroup';
import ContentError from '@components/ContentError';
import CheckboxField from '@components/FormField/CheckboxField';
import LabelSelect from './LabelSelect';

const urlOrigin = window.location.origin;
function WorkflowJobTemplateForm({
  handleSubmit,
  handleCancel,
  i18n,
  submitError,
}) {
  const { id } = useParams();
  const wfjtAddMatch = useRouteMatch('/templates/workflow_job_template/add');

  const [hasContentError, setContentError] = useState(null);

  const [organizationField, organizationMeta, organizationHelpers] = useField(
    'organization'
  );
  const [inventoryField, inventoryMeta, inventoryHelpers] = useField(
    'inventory'
  );
  const [labelsField, , labelsHelpers] = useField('labels');

  const [
    webhookServiceField,
    webhookServiceMeta,
    webhookServiceHelpers,
  ] = useField('webhook_service');

  const [webhookKeyField, webhookKeyMeta, webhookKeyHelpers] = useField(
    'webhookKey'
  );

  const [hasWebhooks, setHasWebhooks] = useState(
    Boolean(webhookServiceField.value)
  );

  const [
    webhookCredentialField,
    webhookCredentialMeta,
    webhookCredentialHelpers,
  ] = useField('webhook_credential');

  const [webhookUrlField, webhookUrlMeta, webhookUrlHelpers] = useField(
    'webhook_url'
  );

  const webhookServiceOptions = [
    {
      value: '',
      key: '',
      label: i18n._(t`Choose a Webhook Service`),
      isDisabled: true,
    },
    {
      value: 'github',
      key: 'github',
      label: i18n._(t`GitHub`),
      isDisabled: false,
    },
    {
      value: 'gitlab',
      key: 'gitlab',
      label: i18n._(t`GitLab`),
      isDisabled: false,
    },
  ];

  const storeWebhookValues = webhookServiceValue => {
    if (
      webhookServiceValue === webhookServiceMeta.initialValue ||
      webhookServiceValue === ''
    ) {
      webhookCredentialHelpers.setValue(webhookCredentialMeta.initialValue);
      webhookUrlHelpers.setValue(webhookUrlMeta.initialValue);
      webhookServiceHelpers.setValue(webhookServiceMeta.initialValue);
      webhookKeyHelpers.setValue(webhookKeyMeta.initialValue);
    } else {
      webhookCredentialHelpers.setValue(null);
      webhookUrlHelpers.setValue(
        `${urlOrigin}/api/v2/workflow_job_templates/${id}/${webhookServiceValue}/`
      );
      webhookKeyHelpers.setValue(
        i18n._(t`a new webhook key will be generated on save.`).toUpperCase()
      );
    }
  };

  const handleWebhookEnablement = (enabledWebhooks, webhookServiceValue) => {
    if (!enabledWebhooks) {
      webhookCredentialHelpers.setValue(null);
      webhookServiceHelpers.setValue('');
      webhookUrlHelpers.setValue('');
      webhookKeyHelpers.setValue('');
    } else {
      storeWebhookValues(webhookServiceValue);
    }
  };

  const {
    request: loadCredentialType,
    error: contentError,
    contentLoading,
    result: credTypeId,
  } = useRequest(
    useCallback(async () => {
      let results;
      if (webhookServiceField.value) {
        results = await CredentialTypesAPI.read({
          namespace: `${webhookServiceField.value}_token`,
        });
        // TODO: Consider how to handle the situation where the results returns
        // and empty array, or any of the other values is undefined or null (data, results, id)
      }
      return results?.data?.results[0]?.id;
    }, [webhookServiceField.value])
  );

  useEffect(() => {
    loadCredentialType();
  }, [loadCredentialType]);

  // TODO: Convert this function below to useRequest. Might want to create a new
  // webhookkey component that handles all of that api calls.  Will also need
  // to move this api call out of WorkflowJobTemplate.jsx and add it to workflowJobTemplateDetai.jsx
  const changeWebhookKey = async () => {
    try {
      const {
        data: { webhook_key: key },
      } = await WorkflowJobTemplatesAPI.updateWebhookKey(id);
      webhookKeyHelpers.setValue(key);
    } catch (err) {
      setContentError(err);
    }
  };

  if (hasContentError || contentError) {
    return <ContentError error={contentError || hasContentError} />;
  }

  if (contentLoading) {
    return <ContentLoading />;
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
          label={i18n._(t`SCM Branch`)}
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
                  t`Enable webhook for this workflow job template.`
                )}
              />
            </span>
          }
          id="wfjt-enabled-webhooks"
          isChecked={Boolean(webhookServiceField.value) || hasWebhooks}
          onChange={checked => {
            setHasWebhooks(checked);
            handleWebhookEnablement(checked, webhookServiceField.value);
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
      {hasWebhooks && (
        <FormColumnLayout>
          <FormGroup
            name="webhook_service"
            fieldId="webhook_service"
            helperTextInvalid={webhookServiceMeta.error}
            isValid={!(webhookServiceMeta.touched || webhookServiceMeta.error)}
            label={i18n._(t`Webhook Service`)}
          >
            <FieldTooltip content={i18n._(t`Select a webhook service`)} />
            <AnsibleSelect
              id="webhook_service"
              data={webhookServiceOptions}
              value={webhookServiceField.value}
              onChange={(event, val) => {
                storeWebhookValues(val);

                webhookServiceHelpers.setValue(val);
              }}
            />
          </FormGroup>
          {!wfjtAddMatch && (
            <>
              <FormGroup
                type="text"
                fieldId="wfjt-webhookURL"
                label={i18n._(t`Webhook URL`)}
                id="wfjt-webhook-url"
                name="webhook_url"
              >
                <FieldTooltip
                  content={i18n._(
                    t`Webhook services can launch jobs with this workflow job template by making a POST request to this URL.`
                  )}
                />
                <TextInput
                  aria-label={i18n._(t`Webhook URL`)}
                  value={webhookUrlField.value}
                  isReadOnly
                />
              </FormGroup>
              <FormGroup
                fieldId="wfjt-webhook-key"
                type="text"
                id="wfjt-webhook-key"
                name="webhookKey"
                label={i18n._(t`Webhook Key`)}
              >
                <FieldTooltip
                  content={i18n._(
                    t`Webhook services can use this as a shared secret.`
                  )}
                />
                <InputGroup>
                  <TextInput
                    isReadOnly
                    aria-label="wfjt-webhook-key"
                    value={webhookKeyField.value}
                  />
                  <Button variant="tertiary" onClick={changeWebhookKey}>
                    <SyncAltIcon />
                  </Button>
                </InputGroup>
              </FormGroup>
            </>
          )}
          {credTypeId && (
            // TODO: Consider how to handle the situation where the results returns
            // an empty array, or any of the other values is undefined or null
            // (data, results, id)
            <CredentialLookup
              label={i18n._(t`Webhook Credential`)}
              tooltip={i18n._(
                t`Optionally select the credential to use to send status updates back to the webhook service.`
              )}
              credentialTypeId={credTypeId}
              onChange={value => {
                webhookCredentialHelpers.setValue(value || null);
              }}
              isValid={!webhookCredentialMeta.error}
              helperTextInvalid={webhookCredentialMeta.error}
              value={webhookCredentialField.value}
            />
          )}
        </FormColumnLayout>
      )}
      {submitError && <FormSubmitError error={submitError} />}
      <FormActionGroup onCancel={handleCancel} onSubmit={handleSubmit} />
    </Form>
  );
}

WorkflowJobTemplateForm.propTypes = {
  handleSubmit: PropTypes.func.isRequired,
  handleCancel: PropTypes.func.isRequired,
  submitError: shape({}),
};

WorkflowJobTemplateForm.defaultProps = {
  submitError: null,
};

const FormikApp = withFormik({
  mapPropsToValues({ template = {}, webhookKey }) {
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
      webhookKey: webhookKey || null,
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
export default withI18n()(withRouter(FormikApp));
