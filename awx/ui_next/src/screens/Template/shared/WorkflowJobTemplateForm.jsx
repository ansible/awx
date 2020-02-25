import React, { useState, useEffect } from 'react';
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

import FormField, {
  FieldTooltip,
  FormSubmitError,
} from '@components/FormField';
import {
  FormColumnLayout,
  FormFullWidthLayout,
  FormCheckboxLayout,
} from '@components/FormLayout';
import OrganizationLookup from '@components/Lookup/OrganizationLookup';
import CredentialLookup from '@components/Lookup/CredentialLookup';
import { InventoryLookup } from '@components/Lookup';
import { VariablesField } from '@components/CodeMirrorInput';
import FormActionGroup from '@components/FormActionGroup';
import ContentError from '@components/ContentError';
import LabelSelect from './LabelSelect';
import CheckboxField from '../../../components/FormField/CheckboxField';

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

  const [contentError, setContentError] = useState(null);
  const [credTypeId, setCredentialTypeId] = useState();

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
      label: i18n._(t`Git Lab`),
      isDisabled: false,
    },
  ];

  useEffect(() => {
    if (!webhookService) {
      return;
    }
    const loadCredentialType = async () => {
      try {
        const {
          data: { results },
        } = await CredentialTypesAPI.read({
          namespace: `${webhookService}_token`,
        });
        setCredentialTypeId(results[0].id);
      } catch (err) {
        setContentError(err);
      }
    };
    loadCredentialType();
  }, [webhookService]);

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

  const setWebhookValues = (form, webhookServiceValue) => {
    if (
      webhookServiceValue === form.initialValues.webhook_service ||
      webhookServiceValue === ''
    ) {
      form.setFieldValue(
        'webhook_credential',
        form.initialValues.webhook_credential
      );
      form.setFieldValue('webhook_url', form.initialValues.webhook_url);
      form.setFieldValue('webhook_service', form.initialValues.webhook_service);

      setWebHookKey(initialWebhookKey);
    } else {
      form.setFieldValue('webhook_credential', null);
      form.setFieldValue(
        'webhook_url',
        `${urlOrigin}/api/v2/workflow_job_templates/${template.id}/${webhookServiceValue}/`
      );

      setWebHookKey('A NEW WEBHOOK KEY WILL BE GENERATED ON SAVE');
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
      form.setFieldValue('webhook_url', '');
      setWebHookService('');
      setWebHookKey('');
    } else {
      setWebhookValues(form, webhookServiceValue);
    }
  };

  if (contentError) {
    return <ContentError error={contentError} />;
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
        extra_vars: template.variables || '---',
        limit: template.limit || '',
        scmBranch: template.scm_branch || '',
        allow_simultaneous: template.allow_simultaneous || false,
        webhook_url:
          template?.related?.webhook_receiver &&
          `${urlOrigin}${template?.related?.webhook_receiver}`,
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
                  isValid={
                    !form.touched.organization || !form.errors.organization
                  }
                  onBlur={() => form.setFieldTouched('organization')}
                  onChange={value => {
                    form.setFieldValue('organization', value.id);
                    setOrganization(value);
                  }}
                  value={organization}
                  touched={form.touched.organization}
                  error={form.errors.organization}
                />
              )}
            </Field>
            <Field name="inventory">
              {({ form }) => (
                <InventoryLookup
                  value={inventory}
                  tooltip={i18n._(
                    t`Select an inventory for the workflow. This inventory is applied to all job template nodes that prompt for an inventory.`
                  )}
                  isValid={!form.touched.inventory || !form.errors.inventory}
                  helperTextInvalid={form.errors.inventory}
                  onChange={value => {
                    form.setFieldValue('inventory', value.id);
                    setInventory(value);
                    form.setFieldValue('organizationId', value.organization);
                  }}
                  error={form.errors.inventory}
                />
              )}
            </Field>
            <FormGroup
              fieldId="wfjt-limit"
              name="limit"
              label={i18n._(t`Limit`)}
            >
              <FieldTooltip
                content={i18n._(
                  t`Provide a host pattern to further constrain the list of hosts that will be managed or affected by the workflow. This limit is applied to all job template nodes that prompt for a limit. Refer to Ansible documentation for more information and examples on patterns.`
                )}
              />
              <FormField type="text" name="limit" id="wfjt-limit" label="" />
            </FormGroup>
            <FormGroup
              fieldId="wfjt-scmBranch"
              id="wfjt-scmBranch"
              label={i18n._(t`SCM Branch`)}
              name="scmBranch"
            >
              <FieldTooltip
                content={i18n._(
                  t`Select a branch for the workflow. This branch is applied to all job template nodes that prompt for a branch.`
                )}
              />
              <FormField
                type="text"
                id="wfjt-scmBranch"
                label=""
                name="scmBranch"
              />
            </FormGroup>
          </FormColumnLayout>
          <FormFullWidthLayout>
            <Field name="labels">
              {({ form, field }) => (
                <FormGroup
                  label={i18n._(t`Labels`)}
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
                    onError={() => setContentError()}
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
            css="margin-top: 20px"
          >
            <Field
              id="wfjt-webhooks"
              name="hasWebhooks"
              label={i18n._(t`Webhooks`)}
            >
              {({ form }) => (
                <Checkbox
                  aria-label={i18n._(t`Webhooks`)}
                  label={
                    <span>
                      {i18n._(t`Webhooks`)}
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
                        setWebhookValues(form, val);

                        form.setFieldValue('webhook_service', val);
                      }}
                    />
                  </FormGroup>
                )}
              </Field>
              {!wfjtAddMatch && (
                <>
                  <FormGroup
                    fieldId="wfjt-webhook-url"
                    id="wfjt-webhook-url"
                    name="webhook_url"
                    label={i18n._(t`Webhook URL`)}
                  >
                    <FieldTooltip
                      content={i18n._(
                        t`Webhook services can launch jobs with this job template by making a POST request to this URL.`
                      )}
                    />
                    <FormField
                      type="text"
                      id="wfjt-webhook-url"
                      name="webhook_url"
                      label=""
                      isReadOnly
                      value="asdfgh"
                    />
                  </FormGroup>
                  <FormGroup
                    fieldId="wfjt-webhook-key"
                    type="text"
                    id="wfjt-webhook-key"
                    name="webhook_key"
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
                </>
              )}
              {credTypeId && (
                <Field name="webhook_credential">
                  {({ form }) => (
                    <FormGroup
                      fieldId="webhook_credential"
                      id="webhook_credential"
                      name="webhook_credential"
                    >
                      <CredentialLookup
                        label={i18n._(t`Webhook Credential`)}
                        tooltip={i18n._(
                          t`Optionally select the credential to use to send status updates back to the webhook service.`
                        )}
                        credentialTypeId={credTypeId || null}
                        onChange={value => {
                          form.setFieldValue('webhook_credential', value.id);
                          setWebhookCredential(value);
                        }}
                        value={webhookCredential}
                      />
                    </FormGroup>
                  )}
                </Field>
              )}
            </FormColumnLayout>
          )}
          <FormSubmitError error={submitError} />
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
