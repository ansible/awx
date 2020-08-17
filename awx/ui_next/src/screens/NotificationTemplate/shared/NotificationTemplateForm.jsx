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
import { NotificationTemplate } from '../../../types';

function NotificationTemplateFormFields({ i18n, defaultMessages }) {
  const [orgField, orgMeta, orgHelpers] = useField('organization');
  const [typeField, typeMeta, typeHelpers] = useField({
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
    console.log(values);
    // onSubmit(values);
  };

  return (
    <Formik
      initialValues={{
        name: template.name,
        description: template.description,
        notification_type: template.notification_type,
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
