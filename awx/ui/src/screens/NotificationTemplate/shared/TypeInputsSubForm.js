import React from 'react';

import { t } from '@lingui/macro';
import { useField } from 'formik';
import { FormGroup, Title } from '@patternfly/react-core';
import {
  FormCheckboxLayout,
  FormColumnLayout,
  FormFullWidthLayout,
  SubFormLayout,
} from 'components/FormLayout';
import FormField, {
  PasswordField,
  CheckboxField,
  ArrayTextField,
} from 'components/FormField';
import AnsibleSelect from 'components/AnsibleSelect';
import { CodeEditorField } from 'components/CodeEditor';
import {
  combine,
  required,
  requiredEmail,
  url,
  minMaxValue,
} from 'util/validators';
import { NotificationType } from 'types';

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

function TypeInputsSubForm({ type }) {
  const Fields = TypeFields[type];
  return (
    <SubFormLayout>
      <Title size="md" headingLevel="h4">
        {t`Type Details`}
      </Title>
      <FormColumnLayout>
        <Fields />
      </FormColumnLayout>
    </SubFormLayout>
  );
}
TypeInputsSubForm.propTypes = {
  type: NotificationType.isRequired,
};

export default TypeInputsSubForm;

function EmailFields() {
  return (
    <>
      <FormField
        id="email-username"
        label={t`Username`}
        name="notification_configuration.username"
        type="text"
      />
      <PasswordField
        id="email-password"
        label={t`Password`}
        name="notification_configuration.password"
      />
      <FormField
        id="email-host"
        label={t`Host`}
        name="notification_configuration.host"
        type="text"
        validate={required(null)}
        isRequired
      />
      <ArrayTextField
        id="email-recipients"
        label={t`Recipient list`}
        name="notification_configuration.recipients"
        type="textarea"
        validate={required(null)}
        isRequired
        rows={3}
        tooltip={t`Enter one email address per line to create a recipient
          list for this type of notification.`}
      />
      <FormField
        id="email-sender"
        label={t`Sender e-mail`}
        name="notification_configuration.sender"
        type="text"
        validate={requiredEmail()}
        isRequired
      />
      <FormField
        id="email-port"
        label={t`Port`}
        name="notification_configuration.port"
        type="number"
        validate={combine([required(null), minMaxValue(1, 65535)])}
        isRequired
        min="0"
        max="65535"
      />
      <FormField
        id="email-timeout"
        label={t`Timeout`}
        name="notification_configuration.timeout"
        type="number"
        validate={combine([required(null), minMaxValue(1, 120)])}
        isRequired
        min="1"
        max="120"
        tooltip={t`The amount of time (in seconds) before the email
          notification stops trying to reach the host and times out. Ranges
          from 1 to 120 seconds.`}
      />
      <FormGroup fieldId="email-options" label={t`E-mail options`}>
        <FormCheckboxLayout>
          <CheckboxField
            id="option-use-ssl"
            name="notification_configuration.use_ssl"
            label={t`Use SSL`}
          />
          <CheckboxField
            id="option-use-tls"
            name="notification_configuration.use_tls"
            label={t`Use TLS`}
          />
        </FormCheckboxLayout>
      </FormGroup>
    </>
  );
}

function GrafanaFields() {
  return (
    <>
      <FormField
        id="grafana-url"
        label={t`Grafana URL`}
        name="notification_configuration.grafana_url"
        type="text"
        validate={required(null)}
        isRequired
        tooltip={t`The base URL of the Grafana server - the
        /api/annotations endpoint will be added automatically to the base
        Grafana URL.`}
      />
      <PasswordField
        id="grafana-key"
        label={t`Grafana API key`}
        name="notification_configuration.grafana_key"
        validate={required(null)}
        isRequired
      />
      <FormField
        id="grafana-dashboard-id"
        label={t`ID of the dashboard (optional)`}
        name="notification_configuration.dashboardId"
        type="text"
      />
      <FormField
        id="grafana-panel-id"
        label={t`ID of the panel (optional)`}
        name="notification_configuration.panelId"
        type="text"
      />
      <ArrayTextField
        id="grafana-tags"
        label={t`Tags for the annotation (optional)`}
        name="notification_configuration.annotation_tags"
        type="textarea"
        rows={3}
        tooltip={t`Enter one Annotation Tag per line, without commas.`}
      />
      <CheckboxField
        id="grafana-ssl"
        label={t`Disable SSL verification`}
        name="notification_configuration.grafana_no_verify_ssl"
      />
    </>
  );
}

function IRCFields() {
  return (
    <>
      <PasswordField
        id="irc-password"
        label={t`IRC server password`}
        name="notification_configuration.password"
      />
      <FormField
        id="irc-port"
        label={t`IRC server port`}
        name="notification_configuration.port"
        type="number"
        validate={required(null)}
        isRequired
        min="0"
      />
      <FormField
        id="irc-server"
        label={t`IRC server address`}
        name="notification_configuration.server"
        type="text"
        validate={required(null)}
        isRequired
      />
      <FormField
        id="irc-nickname"
        label={t`IRC nick`}
        name="notification_configuration.nickname"
        type="text"
        validate={required(null)}
        isRequired
      />
      <ArrayTextField
        id="irc-targets"
        label={t`Destination channels or users`}
        name="notification_configuration.targets"
        type="textarea"
        validate={required(null)}
        isRequired
        tooltip={t`Enter one IRC channel or username per line. The pound
          symbol (#) for channels, and the at (@) symbol for users, are not
          required.`}
      />
      <CheckboxField
        id="grafana-ssl"
        label={t`Disable SSL verification`}
        name="notification_configuration.use_ssl"
      />
    </>
  );
}

function MattermostFields() {
  return (
    <>
      <FormField
        id="mattermost-url"
        label={t`Target URL`}
        name="notification_configuration.mattermost_url"
        type="text"
        validate={combine([required(null), url()])}
        isRequired
      />
      <FormField
        id="mattermost-username"
        label={t`Username`}
        name="notification_configuration.mattermost_username"
        type="text"
      />
      <FormField
        id="mattermost-channel"
        label={t`Channel`}
        name="notification_configuration.mattermost_channel"
        type="text"
      />
      <FormField
        id="mattermost-icon"
        label={t`Icon URL`}
        name="notification_configuration.mattermost_icon_url"
        type="text"
        validate={url()}
      />
      <CheckboxField
        id="mattermost-ssl"
        label={t`Disable SSL verification`}
        name="notification_configuration.mattermost_no_verify_ssl"
      />
    </>
  );
}

function PagerdutyFields() {
  return (
    <>
      <PasswordField
        id="pagerduty-token"
        label={t`API Token`}
        name="notification_configuration.token"
        validate={required(null)}
        isRequired
      />
      <FormField
        id="pagerduty-subdomain"
        label={t`Pagerduty subdomain`}
        name="notification_configuration.subdomain"
        type="text"
        validate={required(null)}
        isRequired
      />
      <FormField
        id="pagerduty-service-key"
        label={t`API service/integration key`}
        name="notification_configuration.service_key"
        type="text"
        validate={required(null)}
        isRequired
      />
      <FormField
        id="pagerduty-identifier"
        label={t`Client identifier`}
        name="notification_configuration.client_name"
        type="text"
        validate={required(null)}
        isRequired
      />
    </>
  );
}

function RocketChatFields() {
  return (
    <>
      <FormField
        id="rocketchat-url"
        label={t`Target URL`}
        name="notification_configuration.rocketchat_url"
        type="text"
        validate={combine([required(null), url()])}
        isRequired
      />
      <FormField
        id="rocketchat-username"
        label={t`Username`}
        name="notification_configuration.rocketchat_username"
        type="text"
      />
      <FormField
        id="rocketchat-icon-url"
        label={t`Icon URL`}
        name="notification_configuration.rocketchat_icon_url"
        type="text"
        validate={url()}
      />
      <CheckboxField
        id="rocketchat-ssl"
        label={t`Disable SSL verification`}
        name="notification_configuration.rocketchat_no_verify_ssl"
      />
    </>
  );
}

function SlackFields() {
  return (
    <>
      <ArrayTextField
        id="slack-channels"
        label={t`Destination channels`}
        name="notification_configuration.channels"
        type="textarea"
        validate={required(null)}
        isRequired
        tooltip={t`Enter one Slack channel per line. The pound symbol (#)
          is required for channels.`}
      />
      <PasswordField
        id="slack-token"
        label={t`Token`}
        name="notification_configuration.token"
        validate={required(null)}
        isRequired
      />
      <FormField
        id="slack-color"
        label={t`Notification color`}
        name="notification_configuration.hex_color"
        type="text"
        tooltip={t`Specify a notification color. Acceptable colors are hex
          color code (example: #3af or #789abc).`}
      />
    </>
  );
}

function TwilioFields() {
  return (
    <>
      <PasswordField
        id="twilio-token"
        label={t`Account token`}
        name="notification_configuration.account_token"
        validate={required(null)}
        isRequired
      />
      <FormField
        id="twilio-from-phone"
        label={t`Source phone number`}
        name="notification_configuration.from_number"
        type="text"
        validate={required(null)}
        isRequired
        tooltip={t`Enter the number associated with the "Messaging
          Service" in Twilio in the format +18005550199.`}
      />
      <ArrayTextField
        id="twilio-destination-numbers"
        label={t`Destination SMS number(s)`}
        name="notification_configuration.to_numbers"
        type="textarea"
        validate={required(null)}
        isRequired
        tooltip={t`Enter one phone number per line to specify where to
          route SMS messages.`}
      />
      <FormField
        id="twilio-account-sid"
        label={t`Account SID`}
        name="notification_configuration.account_sid"
        type="text"
        validate={required(null)}
        isRequired
      />
    </>
  );
}

function WebhookFields() {
  const [methodField, methodMeta] = useField({
    name: 'notification_configuration.http_method',
    validate: required(t`Select a value for this field`),
  });
  return (
    <>
      <FormField
        id="webhook-username"
        label={t`Username`}
        name="notification_configuration.username"
        type="text"
      />
      <PasswordField
        id="webhook-password"
        label={t`Basic auth password`}
        name="notification_configuration.password"
      />
      <FormField
        id="webhook-url"
        label={t`Target URL`}
        name="notification_configuration.url"
        type="text"
        validate={combine([required(null), url()])}
        isRequired
      />
      <CheckboxField
        id="webhook-ssl"
        label={t`Disable SSL verification`}
        name="notification_configuration.disable_ssl_verification"
      />
      <FormFullWidthLayout>
        <CodeEditorField
          id="webhook-headers"
          name="notification_configuration.headers"
          label={t`HTTP Headers`}
          mode="javascript"
          tooltip={t`Specify HTTP Headers in JSON format. Refer to
        the Ansible Tower documentation for example syntax.`}
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
        label={t`HTTP Method`}
      >
        <AnsibleSelect
          {...methodField}
          id="webhook-http-method"
          data={[
            {
              value: '',
              key: '',
              label: t`Choose an HTTP method`,
              isDisabled: true,
            },
            { value: 'POST', key: 'post', label: t`POST` },
            { value: 'PUT', key: 'put', label: t`PUT` },
          ]}
        />
      </FormGroup>
    </>
  );
}
