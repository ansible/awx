const typeFieldNames = {
  email: [
    'username',
    'password',
    'host',
    'recipients',
    'sender',
    'port',
    'timeout',
  ],
  grafana: [
    'grafana_url',
    'grafana_key',
    'dashboardId',
    'panelId',
    'annotation_tags',
    'grafana_no_verify_ssl',
  ],
  irc: ['password', 'port', 'server', 'nickname', 'targets', 'use_ssl'],
  mattermost: [
    'mattermost_url',
    'mattermost_username',
    'mattermost_channel',
    'mattermost_icon_url',
    'mattermost_no_verify_ssl',
  ],
  pagerduty: ['token', 'subdomain', 'service_key', 'client_name'],
  rocketchat: [
    'rocketchat_url',
    'rocketchat_username',
    'rocketchat_icon_url',
    'rocketchat_no_verify_ssl',
  ],
  slack: ['channels', 'token', 'hex_color'],
  twilio: ['account_token', 'from_number', 'to_numbers', 'account_sid'],
  webhook: [
    'username',
    'password',
    'url',
    'disable_ssl_verification',
    'headers',
    'http_method',
  ],
};

export default typeFieldNames;

const initialConfigValues = {};
Object.keys(typeFieldNames).forEach(key => {
  typeFieldNames[key].forEach(fieldName => {
    const isBoolean = fieldName.includes('_ssl');
    initialConfigValues[fieldName] = isBoolean ? false : '';
  });
});

export { initialConfigValues };
