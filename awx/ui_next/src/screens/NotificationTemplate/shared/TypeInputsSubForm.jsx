import React from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { useField } from 'formik';
import { FormGroup, Title } from '@patternfly/react-core';
import {
  FormColumnLayout,
  FormFullWidthLayout,
  SubFormLayout,
} from '../../../components/FormLayout';
import FormField, {
  PasswordField,
  CheckboxField,
  ArrayTextField,
} from '../../../components/FormField';
import AnsibleSelect from '../../../components/AnsibleSelect';
import { CodeMirrorField } from '../../../components/CodeMirrorInput';
import {
  combine,
  required,
  requiredEmail,
  url,
  minMaxValue,
} from '../../../util/validators';
import { NotificationType } from '../../../types';

const TypeFields = {
  email: EmailFields,
  grafana: GrafanaFields,
  irc: IRCFields,
  mattermost: MattermostFields,
  pagerduty: PagerdutyFields,
  rocketchat: RocketChatFields,
  slack: SlackFields,
  twilio: TwilioFields,
  webhook: WebhookFields,
};

function TypeInputsSubForm({ type, i18n }) {
  const Fields = TypeFields[type];
  return (
    <SubFormLayout>
      <Title size="md" headingLevel="h4">
        {i18n._(t`Type Details`)}
      </Title>
      <FormColumnLayout>
        <Fields i18n={i18n} />
      </FormColumnLayout>
    </SubFormLayout>
  );
}
TypeInputsSubForm.propTypes = {
  type: NotificationType.isRequired,
};

export default withI18n()(TypeInputsSubForm);

function EmailFields({ i18n }) {
  const [optionsField, optionsMeta] = useField({
    name: 'emailOptions',
    validate: required(i18n._(t`Select a value for this field`), i18n),
  });
  return (
    <>
      <FormField
        id="email-username"
        label={i18n._(t`Username`)}
        name="notification_configuration.username"
        type="text"
      />
      <PasswordField
        id="email-password"
        label={i18n._(t`Password`)}
        name="notification_configuration.password"
      />
      <FormField
        id="email-host"
        label={i18n._(t`Host`)}
        name="notification_configuration.host"
        type="text"
        validate={required(null, i18n)}
        isRequired
      />
      <ArrayTextField
        id="email-recipients"
        label={i18n._(t`Recipient list`)}
        name="notification_configuration.recipients"
        type="textarea"
        validate={required(null, i18n)}
        isRequired
        rows={3}
        tooltip={i18n._(t`Enter one email address per line to create a recipient
          list for this type of notification.`)}
      />
      <FormField
        id="email-sender"
        label={i18n._(t`Sender e-mail`)}
        name="notification_configuration.sender"
        type="text"
        validate={requiredEmail(i18n)}
        isRequired
      />
      <FormField
        id="email-port"
        label={i18n._(t`Port`)}
        name="notification_configuration.port"
        type="number"
        validate={combine([required(null, i18n), minMaxValue(1, 65535, i18n)])}
        isRequired
        min="0"
        max="65535"
      />
      <FormField
        id="email-timeout"
        label={i18n._(t`Timeout`)}
        name="notification_configuration.timeout"
        type="number"
        validate={combine([required(null, i18n), minMaxValue(1, 120, i18n)])}
        isRequired
        min="1"
        max="120"
        tooltip={i18n._(t`The amount of time (in seconds) before the email
          notification stops trying to reach the host and times out. Ranges
          from 1 to 120 seconds.`)}
      />
      <FormGroup
        fieldId="email-options"
        helperTextInvalid={optionsMeta.error}
        isRequired
        validated={
          !optionsMeta.touched || !optionsMeta.error ? 'default' : 'error'
        }
        label={i18n._(t`E-mail options`)}
      >
        <AnsibleSelect
          {...optionsField}
          id="email-options"
          data={[
            {
              value: '',
              key: '',
              label: i18n._(t`Choose an email option`),
              isDisabled: true,
            },
            { value: 'tls', key: 'tls', label: i18n._(t`Use TLS`) },
            { value: 'ssl', key: 'ssl', label: i18n._(t`Use SSL`) },
          ]}
        />
      </FormGroup>
    </>
  );
}

function GrafanaFields({ i18n }) {
  return (
    <>
      <FormField
        id="grafana-url"
        label={i18n._(t`Grafana URL`)}
        name="notification_configuration.grafana_url"
        type="text"
        validate={required(null, i18n)}
        isRequired
        tooltip={i18n._(t`The base URL of the Grafana server - the
        /api/annotations endpoint will be added automatically to the base
        Grafana URL.`)}
      />
      <PasswordField
        id="grafana-key"
        label={i18n._(t`Grafana API key`)}
        name="notification_configuration.grafana_key"
        validate={required(null, i18n)}
        isRequired
      />
      <FormField
        id="grafana-dashboard-id"
        label={i18n._(t`ID of the dashboard (optional)`)}
        name="notification_configuration.dashboardId"
        type="text"
      />
      <FormField
        id="grafana-panel-id"
        label={i18n._(t`ID of the panel (optional)`)}
        name="notification_configuration.panelId"
        type="text"
      />
      <ArrayTextField
        id="grafana-tags"
        label={i18n._(t`Tags for the annotation (optional)`)}
        name="notification_configuration.annotation_tags"
        type="textarea"
        rows={3}
        tooltip={i18n._(t`Enter one Annotation Tag per line, without commas.`)}
      />
      <CheckboxField
        id="grafana-ssl"
        label={i18n._(t`Disable SSL verification`)}
        name="notification_configuration.grafana_no_verify_ssl"
      />
    </>
  );
}

function IRCFields({ i18n }) {
  return (
    <>
      <PasswordField
        id="irc-password"
        label={i18n._(t`IRC server password`)}
        name="notification_configuration.password"
      />
      <FormField
        id="irc-port"
        label={i18n._(t`IRC server port`)}
        name="notification_configuration.port"
        type="number"
        validate={required(null, i18n)}
        isRequired
        min="0"
      />
      <FormField
        id="irc-server"
        label={i18n._(t`IRC server address`)}
        name="notification_configuration.server"
        type="text"
        validate={required(null, i18n)}
        isRequired
      />
      <FormField
        id="irc-nickname"
        label={i18n._(t`IRC nick`)}
        name="notification_configuration.nickname"
        type="text"
        validate={required(null, i18n)}
        isRequired
      />
      <ArrayTextField
        id="irc-targets"
        label={i18n._(t`Destination channels or users`)}
        name="notification_configuration.targets"
        type="textarea"
        validate={required(null, i18n)}
        isRequired
        tooltip={i18n._(t`Enter one IRC channel or username per line. The pound
          symbol (#) for channels, and the at (@) symbol for users, are not
          required.`)}
      />
      <CheckboxField
        id="grafana-ssl"
        label={i18n._(t`Disable SSL verification`)}
        name="notification_configuration.use_ssl"
      />
    </>
  );
}

function MattermostFields({ i18n }) {
  return (
    <>
      <FormField
        id="mattermost-url"
        label={i18n._(t`Target URL`)}
        name="notification_configuration.mattermost_url"
        type="text"
        validate={combine([required(null, i18n), url(i18n)])}
        isRequired
      />
      <FormField
        id="mattermost-username"
        label={i18n._(t`Username`)}
        name="notification_configuration.mattermost_username"
        type="text"
      />
      <FormField
        id="mattermost-channel"
        label={i18n._(t`Channel`)}
        name="notification_configuration.mattermost_channel"
        type="text"
      />
      <FormField
        id="mattermost-icon"
        label={i18n._(t`Icon URL`)}
        name="notification_configuration.mattermost_icon_url"
        type="text"
        validate={url(i18n)}
      />
      <CheckboxField
        id="mattermost-ssl"
        label={i18n._(t`Disable SSL verification`)}
        name="notification_configuration.mattermost_no_verify_ssl"
      />
    </>
  );
}

function PagerdutyFields({ i18n }) {
  return (
    <>
      <PasswordField
        id="pagerduty-token"
        label={i18n._(t`API Token`)}
        name="notification_configuration.token"
        validate={required(null, i18n)}
        isRequired
      />
      <FormField
        id="pagerduty-subdomain"
        label={i18n._(t`Pagerduty subdomain`)}
        name="notification_configuration.subdomain"
        type="text"
        validate={required(null, i18n)}
        isRequired
      />
      <FormField
        id="pagerduty-service-key"
        label={i18n._(t`API service/integration key`)}
        name="notification_configuration.service_key"
        type="text"
        validate={required(null, i18n)}
        isRequired
      />
      <FormField
        id="pagerduty-identifier"
        label={i18n._(t`Client identifier`)}
        name="notification_configuration.client_name"
        type="text"
        validate={required(null, i18n)}
        isRequired
      />
    </>
  );
}

function RocketChatFields({ i18n }) {
  return (
    <>
      <FormField
        id="rocketchat-url"
        label={i18n._(t`Target URL`)}
        name="notification_configuration.rocketchat_url"
        type="text"
        validate={combine([required(null, i18n), url(i18n)])}
        isRequired
      />
      <FormField
        id="rocketchat-username"
        label={i18n._(t`Username`)}
        name="notification_configuration.rocketchat_username"
        type="text"
      />
      <FormField
        id="rocketchat-icon-url"
        label={i18n._(t`Icon URL`)}
        name="notification_configuration.rocketchat_icon_url"
        type="text"
        validate={url(i18n)}
      />
      <CheckboxField
        id="rocketchat-ssl"
        label={i18n._(t`Disable SSL verification`)}
        name="notification_configuration.rocketchat_no_verify_ssl"
      />
    </>
  );
}

function SlackFields({ i18n }) {
  return (
    <>
      <ArrayTextField
        id="slack-channels"
        label={i18n._(t`Destination channels`)}
        name="notification_configuration.channels"
        type="textarea"
        validate={required(null, i18n)}
        isRequired
        tooltip={i18n._(t`Enter one Slack channel per line. The pound symbol (#)
          is required for channels.`)}
      />
      <PasswordField
        id="slack-token"
        label={i18n._(t`Token`)}
        name="notification_configuration.token"
        validate={required(null, i18n)}
        isRequired
      />
      <FormField
        id="slack-color"
        label={i18n._(t`Notification color`)}
        name="notification_configuration.hex_color"
        type="text"
        tooltip={i18n._(t`Specify a notification color. Acceptable colors are hex
          color code (example: #3af or #789abc).`)}
      />
    </>
  );
}

function TwilioFields({ i18n }) {
  return (
    <>
      <PasswordField
        id="twilio-token"
        label={i18n._(t`Account token`)}
        name="notification_configuration.account_token"
        validate={required(null, i18n)}
        isRequired
      />
      <FormField
        id="twilio-from-phone"
        label={i18n._(t`Source phone number`)}
        name="notification_configuration.from_number"
        type="text"
        validate={required(null, i18n)}
        isRequired
        tooltip={i18n._(t`Enter the number associated with the "Messaging
          Service" in Twilio in the format +18005550199.`)}
      />
      <ArrayTextField
        id="twilio-destination-numbers"
        label={i18n._(t`Destination SMS number(s)`)}
        name="notification_configuration.to_numbers"
        type="textarea"
        validate={required(null, i18n)}
        isRequired
        tooltip={i18n._(t`Enter one phone number per line to specify where to
          route SMS messages.`)}
      />
      <FormField
        id="twilio-account-sid"
        label={i18n._(t`Account SID`)}
        name="notification_configuration.account_sid"
        type="text"
        validate={required(null, i18n)}
        isRequired
      />
    </>
  );
}

function WebhookFields({ i18n }) {
  const [methodField, methodMeta] = useField({
    name: 'notification_configuration.http_method',
    validate: required(i18n._(t`Select a value for this field`), i18n),
  });
  return (
    <>
      <FormField
        id="webhook-username"
        label={i18n._(t`Username`)}
        name="notification_configuration.username"
        type="text"
      />
      <PasswordField
        id="webhook-password"
        label={i18n._(t`Basic auth password`)}
        name="notification_configuration.password"
      />
      <FormField
        id="webhook-url"
        label={i18n._(t`Target URL`)}
        name="notification_configuration.url"
        type="text"
        validate={combine([required(null, i18n), url(i18n)])}
        isRequired
      />
      <CheckboxField
        id="webhook-ssl"
        label={i18n._(t`Disable SSL verification`)}
        name="notification_configuration.disable_ssl_verification"
      />
      <FormFullWidthLayout>
        <CodeMirrorField
          id="webhook-headers"
          name="notification_configuration.headers"
          label={i18n._(t`HTTP Headers`)}
          mode="javascript"
          tooltip={i18n._(t`Specify HTTP Headers in JSON format. Refer to
        the Ansible Tower documentation for example syntax.`)}
          rows={5}
        />
      </FormFullWidthLayout>
      <FormGroup
        fieldId="webhook-http-method"
        helperTextInvalid={methodMeta.error}
        isRequired
        validated={
          !methodMeta.touched || !methodMeta.error ? 'default' : 'error'
        }
        label={i18n._(t`E-mail options`)}
      >
        <AnsibleSelect
          {...methodField}
          id="webhook-http-method"
          data={[
            {
              value: '',
              key: '',
              label: i18n._(t`Choose an HTTP method`),
              isDisabled: true,
            },
            { value: 'POST', key: 'post', label: i18n._(t`POST`) },
            { value: 'PUT', key: 'put', label: i18n._(t`PUT`) },
          ]}
        />
      </FormGroup>
    </>
  );
}
