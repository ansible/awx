import React, { useCallback } from 'react';
import { shape, func } from 'prop-types';
import { Formik, useField, useFormikContext } from 'formik';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Form, FormGroup } from '@patternfly/react-core';

import AnsibleSelect from '../../../components/AnsibleSelect';
import FormField, { FormSubmitError } from '../../../components/FormField';
import FormActionGroup from '../../../components/FormActionGroup/FormActionGroup';
import { OrganizationLookup } from '../../../components/Lookup';
import { required } from '../../../util/validators';
import { FormColumnLayout } from '../../../components/FormLayout';
import TypeInputsSubForm from './TypeInputsSubForm';
import CustomMessagesSubForm from './CustomMessagesSubForm';
import hasCustomMessages from './hasCustomMessages';
import typeFieldNames, { initialConfigValues } from './typeFieldNames';

function NotificationTemplateFormFields({ i18n, defaultMessages, template }) {
  const { setFieldValue } = useFormikContext();
  const [orgField, orgMeta, orgHelpers] = useField('organization');
  const [typeField, typeMeta] = useField({
    name: 'notification_type',
    validate: required(i18n._(t`Select a value for this field`), i18n),
  });

  const onOrganizationChange = useCallback(
    value => {
      setFieldValue('organization', value);
    },
    [setFieldValue]
  );

  return (
    <>
      <FormField
        id="notification-name"
        name="name"
        type="text"
        label={i18n._(t`Name`)}
        validate={required(null, i18n)}
        isRequired
      />
      <FormField
        id="notification-description"
        name="description"
        type="text"
        label={i18n._(t`Description`)}
      />
      <OrganizationLookup
        helperTextInvalid={orgMeta.error}
        isValid={!orgMeta.touched || !orgMeta.error}
        onBlur={() => orgHelpers.setTouched()}
        onChange={onOrganizationChange}
        value={orgField.value}
        touched={orgMeta.touched}
        error={orgMeta.error}
        required
        autoPopulate={!template?.id}
      />
      <FormGroup
        fieldId="notification-type"
        helperTextInvalid={typeMeta.error}
        isRequired
        validated={!typeMeta.touched || !typeMeta.error ? 'default' : 'error'}
        label={i18n._(t`Type`)}
      >
        <AnsibleSelect
          {...typeField}
          id="notification-type"
          isValid={!typeMeta.touched || !typeMeta.error}
          data={[
            {
              value: '',
              key: 'none',
              label: i18n._(t`Choose a Notification Type`),
              isDisabled: true,
            },
            { value: 'email', key: 'email', label: i18n._(t`E-mail`) },
            { value: 'grafana', key: 'grafana', label: 'Grafana' },
            { value: 'irc', key: 'irc', label: 'IRC' },
            { value: 'mattermost', key: 'mattermost', label: 'Mattermost' },
            { value: 'pagerduty', key: 'pagerduty', label: 'Pagerduty' },
            { value: 'rocketchat', key: 'rocketchat', label: 'Rocket.Chat' },
            { value: 'slack', key: 'slack', label: 'Slack' },
            { value: 'twilio', key: 'twilio', label: 'Twilio' },
            { value: 'webhook', key: 'webhook', label: 'Webhook' },
          ]}
        />
      </FormGroup>
      {typeField.value && <TypeInputsSubForm type={typeField.value} />}
      <CustomMessagesSubForm
        defaultMessages={defaultMessages}
        type={typeField.value}
      />
    </>
  );
}

function NotificationTemplateForm({
  template,
  defaultMessages,
  onSubmit,
  onCancel,
  submitError,
  i18n,
}) {
  const handleSubmit = values => {
    onSubmit(
      normalizeFields(
        {
          ...values,
          organization: values.organization?.id,
        },
        defaultMessages
      )
    );
  };

  let emailOptions = '';
  if (template.notification_type === 'email') {
    emailOptions = template.notification_configuration?.use_ssl ? 'ssl' : 'tls';
  }
  const messages = template.messages || { workflow_approval: {} };
  const defs = defaultMessages[template.notification_type || 'email'];
  const mergeDefaultMessages = (templ = {}, def) => {
    return {
      message: templ?.message || def.message || '',
      body: templ?.body || def.body || '',
    };
  };

  const { headers } = template?.notification_configuration || {};

  return (
    <Formik
      initialValues={{
        name: template.name,
        description: template.description,
        notification_type: template.notification_type,
        notification_configuration: {
          ...initialConfigValues,
          ...template.notification_configuration,
          headers: headers ? JSON.stringify(headers, null, 2) : null,
        },
        emailOptions,
        organization: template.summary_fields?.organization,
        messages: {
          started: { ...mergeDefaultMessages(messages.started, defs.started) },
          success: { ...mergeDefaultMessages(messages.success, defs.success) },
          error: { ...mergeDefaultMessages(messages.error, defs.error) },
          workflow_approval: {
            approved: {
              ...mergeDefaultMessages(
                messages.workflow_approval?.approved,
                defs.workflow_approval.approved
              ),
            },
            denied: {
              ...mergeDefaultMessages(
                messages.workflow_approval?.denied,
                defs.workflow_approval.denied
              ),
            },
            running: {
              ...mergeDefaultMessages(
                messages.workflow_approval?.running,
                defs.workflow_approval.running
              ),
            },
            timed_out: {
              ...mergeDefaultMessages(
                messages.workflow_approval?.timed_out,
                defs.workflow_approval.timed_out
              ),
            },
          },
        },
        useCustomMessages: hasCustomMessages(messages, defs),
      }}
      onSubmit={handleSubmit}
    >
      {formik => (
        <Form autoComplete="off" onSubmit={formik.handleSubmit}>
          <FormColumnLayout>
            <NotificationTemplateFormFields
              i18n={i18n}
              defaultMessages={defaultMessages}
              template={template}
            />
            <FormSubmitError error={submitError} />
            <FormActionGroup
              onCancel={onCancel}
              onSubmit={formik.handleSubmit}
            />
          </FormColumnLayout>
        </Form>
      )}
    </Formik>
  );
}

NotificationTemplateForm.propTypes = {
  template: shape(),
  defaultMessages: shape().isRequired,
  onSubmit: func.isRequired,
  onCancel: func.isRequired,
  submitError: shape(),
};

NotificationTemplateForm.defaultProps = {
  template: {
    name: '',
    description: '',
    notification_type: '',
  },
  submitError: null,
};

export default withI18n()(NotificationTemplateForm);

function normalizeFields(values, defaultMessages) {
  return normalizeTypeFields(normalizeMessageFields(values, defaultMessages));
}

/* If the user filled in some of the Type Details fields, then switched
 * to a different notification type, unecessary fields may be set in the
 * notification_configuration — this function strips them off */
function normalizeTypeFields(values) {
  const stripped = {};
  const fields = typeFieldNames[values.notification_type];

  fields.forEach(fieldName => {
    if (typeof values.notification_configuration[fieldName] !== 'undefined') {
      stripped[fieldName] = values.notification_configuration[fieldName];
    }
  });
  if (values.notification_type === 'email') {
    stripped.use_ssl = values.emailOptions === 'ssl';
    stripped.use_tls = !stripped.use_ssl;
  }
  if (values.notification_type === 'webhook') {
    stripped.headers = stripped.headers ? JSON.parse(stripped.headers) : {};
  }
  const { emailOptions, ...rest } = values;

  return {
    ...rest,
    notification_configuration: stripped,
  };
}

function normalizeMessageFields(values, defaults) {
  const { useCustomMessages, ...rest } = values;
  if (!useCustomMessages) {
    return {
      ...rest,
      messages: null,
    };
  }
  const { messages } = values;
  const defs = defaults[values.notification_type];

  const nullIfDefault = (m, d) => {
    return {
      message: m.message === d.message ? null : m.message,
      body: m.body === d.body ? null : m.body,
    };
  };

  const nonDefaultMessages = {
    started: nullIfDefault(messages.started, defs.started),
    success: nullIfDefault(messages.success, defs.success),
    error: nullIfDefault(messages.error, defs.error),
    workflow_approval: {
      approved: nullIfDefault(
        messages.workflow_approval.approved,
        defs.workflow_approval.approved
      ),
      denied: nullIfDefault(
        messages.workflow_approval.denied,
        defs.workflow_approval.denied
      ),
      running: nullIfDefault(
        messages.workflow_approval.running,
        defs.workflow_approval.running
      ),
      timed_out: nullIfDefault(
        messages.workflow_approval.timed_out,
        defs.workflow_approval.timed_out
      ),
    },
  };

  return {
    ...rest,
    messages: nonDefaultMessages,
  };
}
