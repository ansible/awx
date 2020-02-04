import React, { useState, useEffect, useCallback } from 'react';
import { t } from '@lingui/macro';
import { useRouteMatch, useParams } from 'react-router-dom';

import { func, shape } from 'prop-types';

import { withI18n } from '@lingui/react';
import { Formik, Field } from 'formik';
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

function WorkflowJobTemplateForm({
  handleSubmit,
  handleCancel,
  i18n,
  template = {},
  webhook_key,
  submitError,
}) {
  const urlOrigin = window.location.origin;
  const { id } = useParams();
  const wfjtAddMatch = useRouteMatch('/templates/workflow_job_template/add');

  const [hasContentError, setContentError] = useState(null);
  const [webhook_url, setWebhookUrl] = useState(
    template?.related?.webhook_receiver
      ? `${urlOrigin}${template.related.webhook_receiver}`
      : ''
  );
  const [inventory, setInventory] = useState(
    template?.summary_fields?.inventory || null
  );
  const [organization, setOrganization] = useState(
    template?.summary_fields?.organization || null
  );
  const [webhookCredential, setWebhookCredential] = useState(
    template?.summary_fields?.webhook_credential || null
  );
  const [webhookKey, setWebHookKey] = useState(webhook_key);
  const [webhookService, setWebHookService] = useState(
    template.webhook_service || ''
  );
  const [hasWebhooks, setHasWebhooks] = useState(Boolean(webhookService));

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
  const {
    request: loadCredentialType,
    error: contentError,
    contentLoading,
    result: credTypeId,
  } = useRequest(
    useCallback(async () => {
      let results;
      if (webhookService) {
        results = await CredentialTypesAPI.read({
          namespace: `${webhookService}_token`,
        });
        // TODO: Consider how to handle the situation where the results returns
        // and empty array, or any of the other values is undefined or null (data, results, id)
      }
      return results?.data?.results[0]?.id;
    }, [webhookService])
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
      setWebHookKey(key);
    } catch (err) {
      setContentError(err);
    }
  };

  let initialWebhookKey = webhook_key;
  const initialWebhookCredential = template?.summary_fields?.webhook_credential;

  const storeWebhookValues = (form, webhookServiceValue) => {
    if (
      webhookServiceValue === form.initialValues.webhook_service ||
      webhookServiceValue === ''
    ) {
      form.setFieldValue(
        'webhook_credential',
        form.initialValues.webhook_credential
      );
      setWebhookCredential(initialWebhookCredential);

      setWebhookUrl(
        template?.related?.webhook_receiver
          ? `${urlOrigin}${template.related.webhook_receiver}`
          : ''
      );
      form.setFieldValue('webhook_service', form.initialValues.webhook_service);
      setWebHookService(form.initialValues.webhook_service);

      setWebHookKey(initialWebhookKey);
    } else {
      form.setFieldValue('webhook_credential', null);
      setWebhookCredential(null);

      setWebhookUrl(
        `${urlOrigin}/api/v2/workflow_job_templates/${template.id}/${webhookServiceValue}/`
      );

      setWebHookKey(
        i18n._(t`a new webhook key will be generated on save.`).toUpperCase()
      );
    }
  };

  const handleWebhookEnablement = (
    form,
    enabledWebhooks,
    webhookServiceValue
  ) => {
    if (!enabledWebhooks) {
      initialWebhookKey = webhookKey;
      form.setFieldValue('webhook_credential', null);
      form.setFieldValue('webhook_service', '');
      setWebhookUrl('');
      setWebHookService('');
      setWebHookKey('');
    } else {
      storeWebhookValues(form, webhookServiceValue);
    }
  };

  if (hasContentError || contentError) {
    return <ContentError error={contentError || hasContentError} />;
  }

  if (contentLoading) {
    return <ContentLoading />;
  }

  return (
    <Formik
      onSubmit={values => {
        if (values.webhook_service === '') {
          values.webhook_credential = '';
        }
        return handleSubmit(values);
      }}
      initialValues={{
        name: template.name || '',
        description: template.description || '',
        inventory: template?.summary_fields?.inventory?.id || null,
        organization: template?.summary_fields?.organization?.id || null,
        labels: template.summary_fields?.labels?.results || [],
        extra_vars: template.extra_vars || '---',
        limit: template.limit || '',
        scm_branch: template.scm_branch || '',
        allow_simultaneous: template.allow_simultaneous || false,
        webhook_credential:
          template?.summary_fields?.webhook_credential?.id || null,
        webhook_service: template.webhook_service || '',
        ask_limit_on_launch: template.ask_limit_on_launch || false,
        ask_inventory_on_launch: template.ask_inventory_on_launch || false,
        ask_variables_on_launch: template.ask_variables_on_launch || false,
        ask_scm_branch_on_launch: template.ask_scm_branch_on_launch || false,
      }}
    >
      {formik => (
        <Form autoComplete="off" onSubmit={formik.handleSubmit}>
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
            <Field
              id="wfjt-organization"
              label={i18n._(t`Organization`)}
              name="organization"
            >
              {({ form }) => (
                <OrganizationLookup
                  helperTextInvalid={form.errors.organization}
                  onChange={value => {
                    form.setFieldValue('organization', value?.id || null);
                    setOrganization(value);
                  }}
                  value={organization}
                  isValid={!form.errors.organization}
                />
              )}
            </Field>
            <Field name="inventory">
              {({ form }) => (
                <FormGroup
                  label={i18n._(t`Inventory`)}
                  fieldId="wfjt-inventory"
                >
                  <FieldTooltip
                    content={i18n._(
                      t`Select an inventory for the workflow. This inventory is applied to all job template nodes that prompt for an inventory.`
                    )}
                  />
                  <InventoryLookup
                    value={inventory}
                    isValid={!form.errors.inventory}
                    helperTextInvalid={form.errors.inventory}
                    onChange={value => {
                      form.setFieldValue('inventory', value?.id || null);
                      setInventory(value);
                      form.setFieldValue('organizationId', value?.organization);
                    }}
                  />
                </FormGroup>
              )}
            </Field>
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
            <Field name="labels">
              {({ form, field }) => (
                <FormGroup
                  label={i18n._(t`Labels`)}
                  helperTextInvalid={form.errors.webhook_service}
                  isValid={!(form.touched.labels || form.errors.labels)}
                  name="wfjt-labels"
                  fieldId="wfjt-labels"
                >
                  <FieldTooltip
                    content={i18n._(t`Optional labels that describe this job template,
                    such as 'dev' or 'test'. Labels can be used to group and filter
                    job templates and completed jobs.`)}
                  />
                  <LabelSelect
                    value={field.value}
                    onChange={labels => form.setFieldValue('labels', labels)}
                    onError={err => setContentError(err)}
                  />
                </FormGroup>
              )}
            </Field>
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
          <FormCheckboxLayout
            fieldId="options"
            isInline
            label={i18n._(t`Options`)}
          >
            <Field id="wfjt-webhooks" name="hasWebhooks">
              {({ form }) => (
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
                  isChecked={
                    Boolean(form.values.webhook_service) || hasWebhooks
                  }
                  onChange={checked => {
                    setHasWebhooks(checked);
                    handleWebhookEnablement(form, checked, webhookService);
                  }}
                />
              )}
            </Field>

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
              <Field name="webhook_service">
                {({ form, field }) => (
                  <FormGroup
                    name="webhook_service"
                    fieldId="webhook_service"
                    helperTextInvalid={form.errors.webhook_service}
                    isValid={
                      !(
                        form.touched.webhook_service ||
                        form.errors.webhook_service
                      )
                    }
                    label={i18n._(t`Webhook Service`)}
                  >
                    <FieldTooltip
                      content={i18n._(t`Select a webhook service`)}
                    />
                    <AnsibleSelect
                      id="webhook_service"
                      data={webhookServiceOptions}
                      value={field.value}
                      onChange={(event, val) => {
                        setWebHookService(val);
                        storeWebhookValues(form, val);

                        form.setFieldValue('webhook_service', val);
                      }}
                    />
                  </FormGroup>
                )}
              </Field>
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
                      value={webhook_url}
                      isReadOnly
                    />
                  </FormGroup>
                  <Field>
                    {({ form }) => (
                      <FormGroup
                        fieldId="wfjt-webhook-key"
                        type="text"
                        id="wfjt-webhook-key"
                        name="webhook_key"
                        isValid={
                          !(form.touched.webhook_key || form.errors.webhook_key)
                        }
                        helperTextInvalid={form.errors.webhook_service}
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
                            value={webhookKey}
                          />
                          <Button variant="tertiary" onClick={changeWebhookKey}>
                            <SyncAltIcon />
                          </Button>
                        </InputGroup>
                      </FormGroup>
                    )}
                  </Field>
                </>
              )}
              {credTypeId && (
                // TODO: Consider how to handle the situation where the results returns
                // an empty array, or any of the other values is undefined or null
                // (data, results, id)
                <Field name="webhook_credential">
                  {({ form }) => (
                    <CredentialLookup
                      label={i18n._(t`Webhook Credential`)}
                      tooltip={i18n._(
                        t`Optionally select the credential to use to send status updates back to the webhook service.`
                      )}
                      credentialTypeId={credTypeId}
                      onChange={value => {
                        form.setFieldValue(
                          'webhook_credential',
                          value?.id || null
                        );
                        setWebhookCredential(value);
                      }}
                      isValid={!form.errors.webhook_credential}
                      helperTextInvalid={form.errors.webhook_credential}
                      value={webhookCredential}
                    />
                  )}
                </Field>
              )}
            </FormColumnLayout>
          )}
          {submitError && <FormSubmitError error={submitError} />}
          <FormActionGroup
            onCancel={handleCancel}
            onSubmit={formik.handleSubmit}
          />
        </Form>
      )}
    </Formik>
  );
}

WorkflowJobTemplateForm.propTypes = {
  handleSubmit: func.isRequired,
  handleCancel: func.isRequired,
  submitError: shape({}),
};

WorkflowJobTemplateForm.defaultProps = {
  submitError: null,
};

export default withI18n()(WorkflowJobTemplateForm);
