import React, { useState, useCallback } from 'react';
import { Link, useHistory } from 'react-router-dom';
import {
  Button,
  TextList,
  TextListItem,
  TextListItemVariants,
  TextListVariants,
} from '@patternfly/react-core';
import { t } from '@lingui/macro';
import AlertModal from 'components/AlertModal';
import { CardBody, CardActionsRow } from 'components/Card';
import {
  Detail,
  ArrayDetail,
  DetailList,
  DeletedDetail,
  UserDateDetail,
} from 'components/DetailList';
import CodeDetail from 'components/DetailList/CodeDetail';
import DeleteButton from 'components/DeleteButton';
import ErrorDetail from 'components/ErrorDetail';
import { NotificationTemplatesAPI, NotificationsAPI } from 'api';
import useRequest, { useDismissableError } from 'hooks/useRequest';
import StatusLabel from 'components/StatusLabel';
import hasCustomMessages from '../shared/hasCustomMessages';
import { NOTIFICATION_TYPES } from '../constants';
import helpText from '../shared/Notifications.helptext';

const NUM_RETRIES = 25;
const RETRY_TIMEOUT = 5000;

function NotificationTemplateDetail({ template, defaultMessages }) {
  const history = useHistory();
  const [testStatus, setTestStatus] = useState(
    template.summary_fields?.recent_notifications[0]?.status ?? undefined
  );
  const {
    created,
    modified,
    notification_configuration: configuration,
    summary_fields,
    messages,
  } = template;

  const renderOptionsField = configuration.use_ssl || configuration.use_tls;

  const renderOptions = (
    <TextList component={TextListVariants.ul}>
      {configuration.use_ssl && (
        <TextListItem component={TextListItemVariants.li}>
          {t`Use SSL`}
        </TextListItem>
      )}
      {configuration.use_tls && (
        <TextListItem component={TextListItemVariants.li}>
          {t`Use TLS`}
        </TextListItem>
      )}
    </TextList>
  );

  const {
    request: deleteTemplate,
    isLoading,
    error: deleteError,
  } = useRequest(
    useCallback(async () => {
      await NotificationTemplatesAPI.destroy(template.id);
      history.push(`/notification_templates`);
    }, [template.id, history])
  );

  const { request: sendTestNotification, error: testError } = useRequest(
    useCallback(async () => {
      setTestStatus('running');

      let retries = NUM_RETRIES;
      const {
        data: { notification: notificationId },
      } = await NotificationTemplatesAPI.test(template.id);

      async function pollForStatusChange() {
        const { data: notification } = await NotificationsAPI.readDetail(
          notificationId
        );
        if (notification.status !== 'pending') {
          setTestStatus(notification.status);
          return;
        }
        retries--;
        if (retries > 0) {
          setTimeout(pollForStatusChange, RETRY_TIMEOUT);
        }
      }

      setTimeout(pollForStatusChange, RETRY_TIMEOUT);
    }, [template.id])
  );

  const { error, dismissError } = useDismissableError(deleteError || testError);
  const typeMessageDefaults = defaultMessages?.[template?.notification_type];
  return (
    <CardBody>
      <DetailList gutter="sm">
        <Detail label={t`Name`} value={template.name} dataCy="nt-detail-name" />
        <Detail
          label={t`Description`}
          value={template.description}
          dataCy="nt-detail-description"
        />
        {summary_fields.recent_notifications.length ? (
          <Detail
            label={t`Status`}
            value={<StatusLabel status={testStatus} />}
          />
        ) : null}
        {summary_fields.organization ? (
          <Detail
            label={t`Organization`}
            value={
              <Link
                to={`/organizations/${summary_fields.organization.id}/details`}
              >
                {summary_fields.organization.name}
              </Link>
            }
          />
        ) : (
          <DeletedDetail label={t`Organization`} />
        )}
        <Detail
          label={t`Notification Type`}
          value={
            NOTIFICATION_TYPES[template.notification_type] ||
            template.notification_type
          }
          dataCy="nt-detail-type"
        />
        {template.notification_type === 'email' && (
          <>
            <Detail
              label={t`Username`}
              value={configuration.username}
              dataCy="nt-detail-username"
            />
            <Detail
              label={t`Host`}
              value={configuration.host}
              dataCy="nt-detail-host"
            />
            <ArrayDetail
              label={t`Recipient List`}
              helpText={helpText.emailRecepients}
              value={configuration.recipients}
              dataCy="nt-detail-recipients"
            />
            <Detail
              label={t`Sender Email`}
              value={configuration.sender}
              dataCy="nt-detail-sender"
            />
            <Detail
              label={t`Port`}
              value={configuration.port}
              dataCy="nt-detail-port"
            />
            <Detail
              label={t`Timeout`}
              helpText={helpText.emailTimeout}
              value={configuration.timeout}
              dataCy="nt-detail-timeout"
            />
            {renderOptionsField && (
              <Detail
                label={t`Email Options`}
                value={renderOptions}
                helpText={helpText.emailOptions}
              />
            )}
          </>
        )}
        {template.notification_type === 'grafana' && (
          <>
            <Detail
              label={t`Grafana URL`}
              helpText={helpText.grafanaUrl}
              value={configuration.grafana_url}
              dataCy="nt-detail-grafana-url"
            />
            <Detail
              label={t`ID of the Dashboard`}
              value={configuration.dashboardId}
              dataCy="nt-detail-dashboard-id"
            />
            <Detail
              label={t`ID of the Panel`}
              value={configuration.panelId}
              dataCy="nt-detail-panel-id"
            />
            <ArrayDetail
              label={t`Tags for the Annotation`}
              helpText={helpText.grafanaTags}
              value={configuration.annotation_tags}
              dataCy="nt-detail-"
            />
            <Detail
              label={t`Disable SSL Verification`}
              value={configuration.grafana_no_verify_ssl ? t`True` : t`False`}
              dataCy="nt-detail-disable-ssl"
            />
          </>
        )}
        {template.notification_type === 'irc' && (
          <>
            <Detail
              label={t`IRC Server Port`}
              value={configuration.port}
              dataCy="nt-detail-irc-port"
            />
            <Detail
              label={t`IRC Server Address`}
              value={configuration.server}
              dataCy="nt-detail-irc-server"
            />
            <Detail
              label={t`IRC Nick`}
              value={configuration.nickname}
              dataCy="nt-detail-irc-nickname"
            />
            <ArrayDetail
              label={t`Destination Channels or Users`}
              helpText={helpText.ircTargets}
              value={configuration.targets}
              dataCy="nt-detail-channels"
            />
            <Detail
              label={t`SSL Connection`}
              value={configuration.use_ssl ? t`True` : t`False`}
              dataCy="nt-detail-irc-ssl"
            />
          </>
        )}
        {template.notification_type === 'mattermost' && (
          <>
            <Detail
              label={t`Target URL`}
              value={configuration.mattermost_url}
              dataCy="nt-detail-mattermost-url"
            />
            <Detail
              label={t`Username`}
              value={configuration.mattermost_username}
              dataCy="nt-detail-mattermost-username"
            />
            <Detail
              label={t`Channel`}
              value={configuration.mattermost_channel}
              dataCy="nt-detail-mattermost_channel"
            />
            <Detail
              label={t`Icon URL`}
              value={configuration.mattermost_icon_url}
              dataCy="nt-detail-mattermost-icon-url"
            />
            <Detail
              label={t`Disable SSL Verification`}
              value={
                configuration.mattermost_no_verify_ssl ? t`True` : t`False`
              }
              dataCy="nt-detail-disable-ssl"
            />
          </>
        )}
        {template.notification_type === 'pagerduty' && (
          <>
            <Detail
              label={t`Pagerduty Subdomain`}
              value={configuration.subdomain}
              dataCy="nt-detail-pagerduty-subdomain"
            />
            <Detail
              label={t`API Service/Integration Key`}
              value={configuration.service_key}
              dataCy="nt-detail-pagerduty-service-key"
            />
            <Detail
              label={t`Client Identifier`}
              value={configuration.client_name}
              dataCy="nt-detail-pagerduty-client-name"
            />
          </>
        )}
        {template.notification_type === 'rocketchat' && (
          <>
            <Detail
              label={t`Target URL`}
              value={configuration.rocketchat_url}
              dataCy="nt-detail-rocketchat-url"
            />
            <Detail
              label={t`Username`}
              value={configuration.rocketchat_username}
              dataCy="nt-detail-rocketchat-username"
            />
            <Detail
              label={t`Icon URL`}
              value={configuration.rocketchat_icon_url}
              dataCy="nt-detail-rocketchat-icon-url"
            />
            <Detail
              label={t`Disable SSL Verification`}
              value={
                configuration.rocketchat_no_verify_ssl ? t`True` : t`False`
              }
              dataCy="nt-detail-disable-ssl"
            />
          </>
        )}
        {template.notification_type === 'slack' && (
          <>
            <ArrayDetail
              helpText={helpText.slackChannels}
              label={t`Destination Channels`}
              value={configuration.channels}
              dataCy="nt-detail-slack-channels"
            />
            <Detail
              helpText={helpText.slackColor}
              label={t`Notification Color`}
              value={configuration.hex_color}
              dataCy="nt-detail-slack-color"
            />
          </>
        )}
        {template.notification_type === 'twilio' && (
          <>
            <Detail
              label={t`Source Phone Number`}
              helpText={helpText.twilioSourcePhoneNumber}
              value={configuration.from_number}
              dataCy="nt-detail-twilio-source-phone"
            />
            <ArrayDetail
              label={t`Destination SMS Number(s)`}
              helpText={helpText.twilioDestinationNumbers}
              value={configuration.to_numbers}
              dataCy="nt-detail-twilio-destination-numbers"
            />
            <Detail
              label={t`Account SID`}
              value={configuration.account_sid}
              dataCy="nt-detail-twilio-account-sid"
            />
          </>
        )}
        {template.notification_type === 'webhook' && (
          <>
            <Detail
              label={t`Username`}
              value={configuration.username}
              dataCy="nt-detail-webhook-password"
            />
            <Detail
              label={t`Target URL`}
              value={configuration.url}
              dataCy="nt-detail-webhook-url"
            />
            <Detail
              label={t`Disable SSL Verification`}
              value={
                configuration.disable_ssl_verification ? t`True` : t`False`
              }
              dataCy="nt-detail-disable-ssl"
            />
            <Detail
              label={t`HTTP Method`}
              value={configuration.http_method}
              dataCy="nt-detail-webhook-http-method"
            />
            <CodeDetail
              label={t`HTTP Headers`}
              helpText={helpText.webhookHeaders}
              value={JSON.stringify(configuration.headers)}
              mode="json"
              rows={6}
              dataCy="nt-detail-webhook-headers"
            />
          </>
        )}
        <UserDateDetail
          label={t`Created`}
          date={created}
          user={summary_fields?.created_by}
        />
        <UserDateDetail
          label={t`Last Modified`}
          date={modified}
          user={summary_fields?.modified_by}
        />
        {typeMessageDefaults &&
        hasCustomMessages(messages, typeMessageDefaults) ? (
          <CustomMessageDetails
            messages={messages}
            defaults={typeMessageDefaults}
            type={template.notification_type}
          />
        ) : null}
      </DetailList>
      <CardActionsRow>
        {summary_fields.user_capabilities?.edit && (
          <>
            <Button
              ouiaId="notification-template-detail-edit-button"
              component={Link}
              to={`/notification_templates/${template.id}/edit`}
              aria-label={t`Edit`}
            >
              {t`Edit`}
            </Button>
            <Button
              onClick={sendTestNotification}
              variant="secondary"
              isDisabled={testStatus === ('running' || 'pending')}
            >{t`Test`}</Button>
          </>
        )}
        {summary_fields.user_capabilities?.delete && (
          <DeleteButton
            name={template.name}
            modalTitle={t`Delete Notification`}
            onConfirm={deleteTemplate}
            isDisabled={isLoading}
          >
            {t`Delete`}
          </DeleteButton>
        )}
      </CardActionsRow>
      {error && (
        <AlertModal
          isOpen={error}
          variant="error"
          title={t`Error!`}
          onClose={dismissError}
        >
          {deleteError
            ? t`Failed to delete notification.`
            : t`Notification test failed.`}
          <ErrorDetail error={error} />
        </AlertModal>
      )}
    </CardBody>
  );
}

function CustomMessageDetails({ messages, defaults, type }) {
  const showMessages = type !== 'webhook';
  const showBodies = ['email', 'pagerduty', 'webhook'].includes(type);

  return (
    <>
      {showMessages && (
        <CodeDetail
          label={t`Start message`}
          value={messages.started?.message || defaults.started?.message}
          mode="jinja2"
          rows={2}
          fullWidth
        />
      )}
      {showBodies && (
        <CodeDetail
          label={t`Start message body`}
          value={messages.started?.body || defaults.started?.body}
          mode="jinja2"
          rows={6}
          fullWidth
        />
      )}
      {showMessages && (
        <CodeDetail
          label={t`Success message`}
          value={messages.success?.message || defaults.success?.message}
          mode="jinja2"
          rows={2}
          fullWidth
        />
      )}
      {showBodies && (
        <CodeDetail
          label={t`Success message body`}
          value={messages.success?.body || defaults.success?.body}
          mode="jinja2"
          rows={6}
          fullWidth
        />
      )}
      {showMessages && (
        <CodeDetail
          label={t`Error message`}
          value={messages.error?.message || defaults.error?.message}
          mode="jinja2"
          rows={2}
          fullWidth
        />
      )}
      {showBodies && (
        <CodeDetail
          label={t`Error message body`}
          value={messages.error?.body || defaults.error?.body}
          mode="jinja2"
          rows={6}
          fullWidth
        />
      )}
      {showMessages && (
        <CodeDetail
          label={t`Workflow approved message`}
          value={
            messages.workflow_approval?.approved?.message ||
            defaults.workflow_approval.approved.message
          }
          mode="jinja2"
          rows={2}
          fullWidth
        />
      )}
      {showBodies && (
        <CodeDetail
          label={t`Workflow approved message body`}
          value={
            messages.workflow_approval?.approved?.body ||
            defaults.workflow_approval.approved.body
          }
          mode="jinja2"
          rows={6}
          fullWidth
        />
      )}
      {showMessages && (
        <CodeDetail
          label={t`Workflow denied message`}
          value={
            messages.workflow_approval?.denied?.message ||
            defaults.workflow_approval.denied.message
          }
          mode="jinja2"
          rows={2}
          fullWidth
        />
      )}
      {showBodies && (
        <CodeDetail
          label={t`Workflow denied message body`}
          value={
            messages.workflow_approval?.denied?.body ||
            defaults.workflow_approval.denied.body
          }
          mode="jinja2"
          rows={6}
          fullWidth
        />
      )}
      {showMessages && (
        <CodeDetail
          label={t`Workflow pending message`}
          value={
            messages.workflow_approval?.running?.message ||
            defaults.workflow_approval.running.message
          }
          mode="jinja2"
          rows={2}
          fullWidth
        />
      )}
      {showBodies && (
        <CodeDetail
          label={t`Workflow pending message body`}
          value={
            messages.workflow_approval?.running?.body ||
            defaults.workflow_approval.running.body
          }
          mode="jinja2"
          rows={6}
          fullWidth
        />
      )}
      {showMessages && (
        <CodeDetail
          label={t`Workflow timed out message`}
          value={
            messages.workflow_approval?.timed_out?.message ||
            defaults.workflow_approval.timed_out.message
          }
          mode="jinja2"
          rows={2}
          fullWidth
        />
      )}
      {showBodies && (
        <CodeDetail
          label={t`Workflow timed out message body`}
          value={
            messages.workflow_approval?.timed_out?.body ||
            defaults.workflow_approval.timed_out.body
          }
          mode="jinja2"
          rows={6}
          fullWidth
        />
      )}
    </>
  );
}

export default NotificationTemplateDetail;
