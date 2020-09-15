import React, { useCallback } from 'react';
import { Link, useHistory } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { Button } from '@patternfly/react-core';
import { t } from '@lingui/macro';
import AlertModal from '../../../components/AlertModal';
import { CardBody, CardActionsRow } from '../../../components/Card';
import {
  Detail,
  ArrayDetail,
  DetailList,
  DeletedDetail,
} from '../../../components/DetailList';
import CodeDetail from '../../../components/DetailList/CodeDetail';
import DeleteButton from '../../../components/DeleteButton';
import ErrorDetail from '../../../components/ErrorDetail';
import { NotificationTemplatesAPI } from '../../../api';
import useRequest, { useDismissableError } from '../../../util/useRequest';
import hasCustomMessages from '../shared/hasCustomMessages';
import { NOTIFICATION_TYPES } from '../constants';

function NotificationTemplateDetail({ i18n, template, defaultMessages }) {
  const history = useHistory();

  const {
    notification_configuration: configuration,
    summary_fields,
    messages,
  } = template;

  const { request: deleteTemplate, isLoading, error: deleteError } = useRequest(
    useCallback(async () => {
      await NotificationTemplatesAPI.destroy(template.id);
      history.push(`/notification_templates`);
    }, [template.id, history])
  );

  const { error, dismissError } = useDismissableError(deleteError);
  const typeMessageDefaults = defaultMessages[template.notification_type];

  return (
    <CardBody>
      <DetailList gutter="sm">
        <Detail
          label={i18n._(t`Name`)}
          value={template.name}
          dataCy="nt-detail-name"
        />
        <Detail
          label={i18n._(t`Description`)}
          value={template.description}
          dataCy="nt-detail-description"
        />
        {summary_fields.organization ? (
          <Detail
            label={i18n._(t`Organization`)}
            value={
              <Link
                to={`/organizations/${summary_fields.organization.id}/details`}
              >
                {summary_fields.organization.name}
              </Link>
            }
          />
        ) : (
          <DeletedDetail label={i18n._(t`Organization`)} />
        )}
        <Detail
          label={i18n._(t`Notification Type`)}
          value={
            NOTIFICATION_TYPES[template.notification_type] ||
            template.notification_type
          }
          dataCy="nt-detail-type"
        />
        {template.notification_type === 'email' && (
          <>
            <Detail
              label={i18n._(t`Username`)}
              value={configuration.username}
              dataCy="nt-detail-username"
            />
            <Detail
              label={i18n._(t`Host`)}
              value={configuration.host}
              dataCy="nt-detail-host"
            />
            <ArrayDetail
              label={i18n._(t`Recipient List`)}
              value={configuration.recipients}
              dataCy="nt-detail-recipients"
            />
            <Detail
              label={i18n._(t`Sender Email`)}
              value={configuration.sender}
              dataCy="nt-detail-sender"
            />
            <Detail
              label={i18n._(t`Port`)}
              value={configuration.port}
              dataCy="nt-detail-port"
            />
            <Detail
              label={i18n._(t`Timeout`)}
              value={configuration.timeout}
              dataCy="nt-detail-timeout"
            />
            <Detail
              label={i18n._(t`Email Options`)}
              value={
                configuration.use_ssl ? i18n._(t`Use SSL`) : i18n._(t`Use TLS`)
              }
              dataCy="nt-detail-email-options"
            />
          </>
        )}
        {template.notification_type === 'grafana' && (
          <>
            <Detail
              label={i18n._(t`Grafana URL`)}
              value={configuration.grafana_url}
              dataCy="nt-detail-grafana-url"
            />
            <Detail
              label={i18n._(t`ID of the Dashboard`)}
              value={configuration.dashboardId}
              dataCy="nt-detail-dashboard-id"
            />
            <Detail
              label={i18n._(t`ID of the Panel`)}
              value={configuration.panelId}
              dataCy="nt-detail-panel-id"
            />
            <ArrayDetail
              label={i18n._(t`Tags for the Annotation`)}
              value={configuration.annotation_tags}
              dataCy="nt-detail-"
            />
            <Detail
              label={i18n._(t`Disable SSL Verification`)}
              value={
                configuration.grafana_no_verify_ssl
                  ? i18n._(t`True`)
                  : i18n._(t`False`)
              }
              dataCy="nt-detail-disable-ssl"
            />
          </>
        )}
        {template.notification_type === 'irc' && (
          <>
            <Detail
              label={i18n._(t`IRC Server Port`)}
              value={configuration.port}
              dataCy="nt-detail-irc-port"
            />
            <Detail
              label={i18n._(t`IRC Server Address`)}
              value={configuration.server}
              dataCy="nt-detail-irc-server"
            />
            <Detail
              label={i18n._(t`IRC Nick`)}
              value={configuration.nickname}
              dataCy="nt-detail-irc-nickname"
            />
            <ArrayDetail
              label={i18n._(t`Destination Channels or Users`)}
              value={configuration.targets}
              dataCy="nt-detail-channels"
            />
            <Detail
              label={i18n._(t`SSL Connection`)}
              value={configuration.use_ssl ? i18n._(t`True`) : i18n._(t`False`)}
              dataCy="nt-detail-irc-ssl"
            />
          </>
        )}
        {template.notification_type === 'mattermost' && (
          <>
            <Detail
              label={i18n._(t`Target URL`)}
              value={configuration.mattermost_url}
              dataCy="nt-detail-mattermost-url"
            />
            <Detail
              label={i18n._(t`Username`)}
              value={configuration.mattermost_username}
              dataCy="nt-detail-mattermost-username"
            />
            <Detail
              label={i18n._(t`Channel`)}
              value={configuration.mattermost_channel}
              dataCy="nt-detail-mattermost_channel"
            />
            <Detail
              label={i18n._(t`Icon URL`)}
              value={configuration.mattermost_icon_url}
              dataCy="nt-detail-mattermost-icon-url"
            />
            <Detail
              label={i18n._(t`Disable SSL Verification`)}
              value={
                configuration.mattermost_no_verify_ssl
                  ? i18n._(t`True`)
                  : i18n._(t`False`)
              }
              dataCy="nt-detail-disable-ssl"
            />
          </>
        )}
        {template.notification_type === 'pagerduty' && (
          <>
            <Detail
              label={i18n._(t`Pagerduty Subdomain`)}
              value={configuration.subdomain}
              dataCy="nt-detail-pagerduty-subdomain"
            />
            <Detail
              label={i18n._(t`API Service/Integration Key`)}
              value={configuration.service_key}
              dataCy="nt-detail-pagerduty-service-key"
            />
            <Detail
              label={i18n._(t`Client Identifier`)}
              value={configuration.client_name}
              dataCy="nt-detail-pagerduty-client-name"
            />
          </>
        )}
        {template.notification_type === 'rocketchat' && (
          <>
            <Detail
              label={i18n._(t`Target URL`)}
              value={configuration.rocketchat_url}
              dataCy="nt-detail-rocketchat-url"
            />
            <Detail
              label={i18n._(t`Username`)}
              value={configuration.rocketchat_username}
              dataCy="nt-detail-rocketchat-username"
            />
            <Detail
              label={i18n._(t`Icon URL`)}
              value={configuration.rocketchat_icon_url}
              dataCy="nt-detail-rocketchat-icon-url"
            />
            <Detail
              label={i18n._(t`Disable SSL Verification`)}
              value={
                configuration.rocketchat_no_verify_ssl
                  ? i18n._(t`True`)
                  : i18n._(t`False`)
              }
              dataCy="nt-detail-disable-ssl"
            />
          </>
        )}
        {template.notification_type === 'slack' && (
          <>
            <ArrayDetail
              label={i18n._(t`Destination Channels`)}
              value={configuration.channels}
              dataCy="nt-detail-slack-channels"
            />
            <Detail
              label={i18n._(t`Notification Color`)}
              value={configuration.hex_color}
              dataCy="nt-detail-slack-color"
            />
          </>
        )}
        {template.notification_type === 'twilio' && (
          <>
            <Detail
              label={i18n._(t`Source Phone Number`)}
              value={configuration.from_number}
              dataCy="nt-detail-twilio-source-phone"
            />
            <ArrayDetail
              label={i18n._(t`Destination SMS Number(s)`)}
              value={configuration.to_numbers}
              dataCy="nt-detail-twilio-destination-numbers"
            />
            <Detail
              label={i18n._(t`Account SID`)}
              value={configuration.account_sid}
              dataCy="nt-detail-twilio-account-sid"
            />
          </>
        )}
        {template.notification_type === 'webhook' && (
          <>
            <Detail
              label={i18n._(t`Username`)}
              value={configuration.username}
              dataCy="nt-detail-webhook-password"
            />
            <Detail
              label={i18n._(t`Target URL`)}
              value={configuration.url}
              dataCy="nt-detail-webhook-url"
            />
            <Detail
              label={i18n._(t`Disable SSL Verification`)}
              value={
                configuration.disable_ssl_verification
                  ? i18n._(t`True`)
                  : i18n._(t`False`)
              }
              dataCy="nt-detail-disable-ssl"
            />
            <Detail
              label={i18n._(t`HTTP Method`)}
              value={configuration.http_method}
              dataCy="nt-detail-webhook-http-method"
            />
            <CodeDetail
              label={i18n._(t`HTTP Headers`)}
              value={JSON.stringify(configuration.headers)}
              mode="json"
              rows="6"
              dataCy="nt-detail-webhook-headers"
            />
          </>
        )}
        {hasCustomMessages(messages, typeMessageDefaults) && (
          <CustomMessageDetails
            messages={messages}
            defaults={typeMessageDefaults}
            type={template.notification_type}
            i18n={i18n}
          />
        )}
      </DetailList>
      <CardActionsRow>
        {summary_fields.user_capabilities &&
          summary_fields.user_capabilities.edit && (
            <Button
              component={Link}
              to={`/notification_templates/${template.id}/edit`}
              aria-label={i18n._(t`Edit`)}
            >
              {i18n._(t`Edit`)}
            </Button>
          )}
        {summary_fields.user_capabilities &&
          summary_fields.user_capabilities.delete && (
            <DeleteButton
              name={template.name}
              modalTitle={i18n._(t`Delete Notification`)}
              onConfirm={deleteTemplate}
              isDisabled={isLoading}
            >
              {i18n._(t`Delete`)}
            </DeleteButton>
          )}
      </CardActionsRow>
      {error && (
        <AlertModal
          isOpen={error}
          variant="error"
          title={i18n._(t`Error!`)}
          onClose={dismissError}
        >
          {i18n._(t`Failed to delete notification.`)}
          <ErrorDetail error={error} />
        </AlertModal>
      )}
    </CardBody>
  );
}

function CustomMessageDetails({ messages, defaults, type, i18n }) {
  const showMessages = type !== 'webhook';
  const showBodies = ['email', 'pagerduty', 'webhook'].includes(type);

  return (
    <>
      {showMessages && (
        <CodeDetail
          label={i18n._(t`Start message`)}
          value={messages.started.message || defaults.started.message}
          mode="jinja2"
          rows="2"
          fullWidth
        />
      )}
      {showBodies && (
        <CodeDetail
          label={i18n._(t`Start message body`)}
          value={messages.started.body || defaults.started.body}
          mode="jinja2"
          rows="6"
          fullWidth
        />
      )}
      {showMessages && (
        <CodeDetail
          label={i18n._(t`Success message`)}
          value={messages.success.message || defaults.success.message}
          mode="jinja2"
          rows="2"
          fullWidth
        />
      )}
      {showBodies && (
        <CodeDetail
          label={i18n._(t`Success message body`)}
          value={messages.success.body || defaults.success.body}
          mode="jinja2"
          rows="6"
          fullWidth
        />
      )}
      {showMessages && (
        <CodeDetail
          label={i18n._(t`Error message`)}
          value={messages.error.message || defaults.error.message}
          mode="jinja2"
          rows="2"
          fullWidth
        />
      )}
      {showBodies && (
        <CodeDetail
          label={i18n._(t`Error message body`)}
          value={messages.error.body || defaults.error.body}
          mode="jinja2"
          rows="6"
          fullWidth
        />
      )}
      {showMessages && (
        <CodeDetail
          label={i18n._(t`Workflow approved message`)}
          value={
            messages.workflow_approval?.approved?.message ||
            defaults.workflow_approval.approved.message
          }
          mode="jinja2"
          rows="2"
          fullWidth
        />
      )}
      {showBodies && (
        <CodeDetail
          label={i18n._(t`Workflow approved message body`)}
          value={
            messages.workflow_approval?.approved?.body ||
            defaults.workflow_approval.approved.body
          }
          mode="jinja2"
          rows="6"
          fullWidth
        />
      )}
      {showMessages && (
        <CodeDetail
          label={i18n._(t`Workflow denied message`)}
          value={
            messages.workflow_approval?.denied?.message ||
            defaults.workflow_approval.denied.message
          }
          mode="jinja2"
          rows="2"
          fullWidth
        />
      )}
      {showBodies && (
        <CodeDetail
          label={i18n._(t`Workflow denied message body`)}
          value={
            messages.workflow_approval?.denied?.body ||
            defaults.workflow_approval.denied.body
          }
          mode="jinja2"
          rows="6"
          fullWidth
        />
      )}
      {showMessages && (
        <CodeDetail
          label={i18n._(t`Workflow pending message`)}
          value={
            messages.workflow_approval?.running?.message ||
            defaults.workflow_approval.running.message
          }
          mode="jinja2"
          rows="2"
          fullWidth
        />
      )}
      {showBodies && (
        <CodeDetail
          label={i18n._(t`Workflow pending message body`)}
          value={
            messages.workflow_approval?.running?.body ||
            defaults.workflow_approval.running.body
          }
          mode="jinja2"
          rows="6"
          fullWidth
        />
      )}
      {showMessages && (
        <CodeDetail
          label={i18n._(t`Workflow timed out message`)}
          value={
            messages.workflow_approval?.timed_out?.message ||
            defaults.workflow_approval.timed_out.message
          }
          mode="jinja2"
          rows="2"
          fullWidth
        />
      )}
      {showBodies && (
        <CodeDetail
          label={i18n._(t`Workflow timed out message body`)}
          value={
            messages.workflow_approval?.timed_out?.body ||
            defaults.workflow_approval.timed_out.body
          }
          mode="jinja2"
          rows="6"
          fullWidth
        />
      )}
    </>
  );
}

export default withI18n()(NotificationTemplateDetail);
