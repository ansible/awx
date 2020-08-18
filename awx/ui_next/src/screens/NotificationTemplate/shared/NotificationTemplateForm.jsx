import React, { useContext, useEffect, useState } from 'react';
import { shape, func } from 'prop-types';
import { Formik, useField } from 'formik';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Form, FormGroup } from '@patternfly/react-core';

import { OrganizationsAPI } from '../../../api';
import { ConfigContext } from '../../../contexts/Config';
import AnsibleSelect from '../../../components/AnsibleSelect';
import ContentError from '../../../components/ContentError';
import ContentLoading from '../../../components/ContentLoading';
import FormField, { FormSubmitError } from '../../../components/FormField';
import FormActionGroup from '../../../components/FormActionGroup/FormActionGroup';
import { OrganizationLookup } from '../../../components/Lookup';
import { getAddedAndRemoved } from '../../../util/lists';
import { required, minMaxValue } from '../../../util/validators';
import { FormColumnLayout } from '../../../components/FormLayout';
import TypeInputsSubForm from './TypeInputsSubForm';
import typeFieldNames, { initialConfigValues } from './typeFieldNames';
import { NotificationTemplate } from '../../../types';

function NotificationTemplateFormFields({ i18n, defaultMessages }) {
  const [orgField, orgMeta, orgHelpers] = useField('organization');
  const [typeField, typeMeta] = useField({
    name: 'notification_type',
    validate: required(i18n._(t`Select a value for this field`), i18n),
  });

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
        onChange={value => {
          orgHelpers.setValue(value);
        }}
        value={orgField.value}
        touched={orgMeta.touched}
        error={orgMeta.error}
        required
      />
      <FormGroup
        fieldId="notification-type"
        helperTextInvalid={typeMeta.error}
        isRequired
        validated={!typeMeta.touched || typeMeta.error ? 'default' : 'error'}
        label={i18n._(t`Type`)}
      >
        <AnsibleSelect
          {...typeField}
          id="notification-type"
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
    onSubmit(normalizeTypeFields(values));
  };

  let emailOptions = '';
  if (template.notification_type === 'email') {
    emailOptions = template.notification_configuration.use_ssl ? 'ssl' : 'tls';
  }

  return (
    <Formik
      initialValues={{
        name: template.name,
        description: template.description,
        notification_type: template.notification_type,
        notification_configuration: {
          ...initialConfigValues,
          ...template.notification_configuration,
        },
        emailOptions,
      }}
      onSubmit={handleSubmit}
    >
      {formik => (
        <Form autoComplete="off" onSubmit={formik.handleSubmit}>
          <FormColumnLayout>
            <NotificationTemplateFormFields i18n={i18n} />
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
  template: NotificationTemplate,
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

/* If the user filled in some of the Type Details fields, then switched
 * to a different notification type, unecessary fields may be set in the
 * notification_configuration — this function strips them off */
function normalizeTypeFields(values) {
  const stripped = {};
  const fields = typeFieldNames[values.notification_type];
  fields.foreach(fieldName => {
    if (typeof values[fieldName] !== 'undefined') {
      stripped[fieldName] = values[fieldName];
    }
  });
  if (values.notification_type === 'email') {
    stripped.use_ssl = values.emailOptions === 'ssl';
    stripped.use_tls = !stripped.use_ssl;
  }

  return {
    ...values,
    notification_configuration: stripped,
  };
}
