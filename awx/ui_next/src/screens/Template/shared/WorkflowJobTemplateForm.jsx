import React, { useState, useEffect } from 'react';
import { t } from '@lingui/macro';
import { func, shape } from 'prop-types';

import { withI18n } from '@lingui/react';
import { Formik, Field } from 'formik';
import {
  Form,
  FormGroup,
  Checkbox,
  InputGroup,
  Button,
  TextInput,
} from '@patternfly/react-core';
import { required } from '@util/validators';
import { SyncAltIcon } from '@patternfly/react-icons';
import { useParams } from 'react-router-dom';

import AnsibleSelect from '@components/AnsibleSelect';
import { WorkflowJobTemplatesAPI, CredentialTypesAPI } from '@api';
import FormRow from '@components/FormRow';

import FormField, {
  FieldTooltip,
  FormSubmitError,
} from '@components/FormField';
import OrganizationLookup from '@components/Lookup/OrganizationLookup';
import CredentialLookup from '@components/Lookup/CredentialLookup';
import { InventoryLookup } from '@components/Lookup';
import { VariablesField } from '@components/CodeMirrorInput';
import FormActionGroup from '@components/FormActionGroup';
import ContentError from '@components/ContentError';
import styled from 'styled-components';
import LabelSelect from './LabelSelect';

const GridFormGroup = styled(FormGroup)`
  & > label {
    grid-column: 1 / -1;
  }

  && {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  }
`;

function WorkflowJobTemplateForm({
  handleSubmit,
  handleCancel,
  i18n,
  template = {},
  webhook_key,
  submitError,
}) {
  const { id } = useParams();
  const urlOrigin = window.location.origin;
  const [contentError, setContentError] = useState(null);
  const [inventory, setInventory] = useState(
    template?.summary_fields?.inventory || null
  );
  const [organization, setOrganization] = useState(
    template?.summary_fields?.organization || null
  );
  const [webHookKey, setWebHookKey] = useState(webhook_key);
  const [credTypeId, setCredentialTypeId] = useState();
  const [webhookService, setWebHookService] = useState(
    template.webhook_service || ''
  );
  const [hasWebhooks, setHasWebhooks] = useState(
    webhookService !== '' || false
  );
  const [webhookCredential, setWebHookCredential] = useState(
    template?.summary_fields?.webhook_credential || null
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
      namespace: 'git_hub',
      label: i18n._(t`GitHub`),
      isDisabled: false,
    },
    {
      value: 'gitlab',
      key: 'gitlab',
      namespace: 'git_lab',
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
          namespace: webhookService.includes('hub')
            ? 'github_token'
            : 'gitlab_token',
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

  if (contentError) {
    return <ContentError error={contentError} />;
  }

  return (
    <Formik
      onSubmit={handleSubmit}
      initialValues={{
        name: template.name || '',
        description: template.description || '',
        inventory: template.summary_fields?.inventory?.id || '',
        organization: template.summary_fields?.organization?.id || '',
        labels: template.summary_fields?.labels?.results || [],
        variables: template.variables || '---',
        limit: template.limit || '',
        scmBranch: template.scm_branch || '',
        allow_simultaneous: template.allow_simultaneous || false,
        webhook_url:
          template?.related?.webhook_receiver &&
          `${urlOrigin}${template?.related?.webhook_receiver}`,
        webhook_credential:
          template?.summary_fields?.webhook_credential?.id || null,
        webhook_service: webhookService,
        ask_limit_on_launch: template.ask_limit_on_launch || false,
        ask_inventory_on_launch: template.ask_inventory_on_launch || false,
        ask_variables_on_launch: template.ask_variables_on_launch || false,
        ask_scm_branch_on_launch: template.ask_scm_branch_on_launch || false,
      }}
    >
      {formik => (
        <Form autoComplete="off" onSubmit={formik.handleSubmit}>
          <FormRow>
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
                    form.setFieldValue('organization', value?.id || null);
                    setOrganization(value);
                  }}
                  value={organization}
                  touched={form.touched.organization}
                  error={form.errors.organization}
                />
              )}
            </Field>
          </FormRow>
          <FormRow>
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
                    form.setFieldValue('inventory', value?.id || null);
                    form.setFieldValue(
                      'organizationId',
                      value?.organization || null
                    );
                    setInventory(value);
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
          </FormRow>

          <FormRow>
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
          </FormRow>
          <FormRow>
            <VariablesField
              id="wfjt-variables"
              name="variables"
              label={i18n._(t`Variables`)}
            />
          </FormRow>
          <GridFormGroup
            fieldId="options"
            isInline
            label={i18n._(t`Options`)}
            css="margin-top: 20px"
          >
            <Checkbox
              id="wfjt-webhooks"
              name="has_webhooks"
              label={
                <span>
                  {i18n._(t`Webhooks`)} &nbsp;
                  <FieldTooltip
                    content={i18n._(
                      t`Enable webhook for this workflow job template.`
                    )}
                  />
                </span>
              }
              isChecked={hasWebhooks}
              onChange={checked => {
                setHasWebhooks(checked);
              }}
            />
            <Field name="allow_simultaneous">
              {({ field, form }) => (
                <Checkbox
                  name="allow_simultaneous"
                  id="wfjt-allow_simultaneous"
                  label={
                    <span>
                      {i18n._(t`Enable Concurrent Jobs`)} &nbsp;
                      <FieldTooltip
                        content={i18n._(
                          t`If enabled, simultaneous runs of this workflow job template will be allowed.`
                        )}
                      />
                    </span>
                  }
                  isChecked={field.value}
                  onChange={value => {
                    form.setFieldValue('allow_simultaneous', value);
                  }}
                />
              )}
            </Field>
          </GridFormGroup>
          {hasWebhooks && (
            <>
              <FormRow>
                {template.related && (
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
                    />
                  </FormGroup>
                )}
                {template.related && (
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
                        value={webHookKey}
                      />
                      <Button variant="tertiary" onClick={changeWebhookKey}>
                        <SyncAltIcon />
                      </Button>
                    </InputGroup>
                  </FormGroup>
                )}
                <Field name="webhook_service">
                  {({ form }) => (
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
                        value={webhookService}
                        onChange={(event, val) => {
                          setWebHookService(val);
                          setWebHookCredential(null);
                          form.setFieldValue('webhook_service', val);
                          form.setFieldValue('webhook_credential', null);
                        }}
                      />
                    </FormGroup>
                  )}
                </Field>
              </FormRow>
              {credTypeId && (
                <FormRow>
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
                            setWebHookCredential(value);
                            form.setFieldValue('webhook_credential', value.id);
                          }}
                          value={webhookCredential}
                        />
                      </FormGroup>
                    )}
                  </Field>
                </FormRow>
              )}
            </>
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
