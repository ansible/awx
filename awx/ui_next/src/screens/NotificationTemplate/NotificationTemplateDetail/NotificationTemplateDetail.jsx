import React, { useState, useEffect, useCallback } from 'react';
import { Link, useHistory } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import {
  Button,
  Chip,
  TextList,
  TextListItem,
  TextListItemVariants,
  TextListVariants,
  Label,
} from '@patternfly/react-core';
import { t } from '@lingui/macro';

import AlertModal from '../../../components/AlertModal';
import { CardBody, CardActionsRow } from '../../../components/Card';
import ChipGroup from '../../../components/ChipGroup';
import ContentError from '../../../components/ContentError';
import ContentLoading from '../../../components/ContentLoading';
import CredentialChip from '../../../components/CredentialChip';
import {
  Detail,
  DetailList,
  DeletedDetail,
  UserDateDetail,
} from '../../../components/DetailList';
import DeleteButton from '../../../components/DeleteButton';
import ErrorDetail from '../../../components/ErrorDetail';
import LaunchButton from '../../../components/LaunchButton';
import { VariablesDetail } from '../../../components/CodeMirrorInput';
import { NotificationTemplatesAPI } from '../../../api';
import useRequest, { useDismissableError } from '../../../util/useRequest';
import { NOTIFICATION_TYPES } from '../constants';

function NotificationTemplateDetail({ i18n, template }) {
  const history = useHistory();

  const {
    notification_configuration: configuration,
    summary_fields,
  } = template;

  const { request: deleteTemplate, isLoading, error: deleteError } = useRequest(
    useCallback(async () => {
      await NotificationTemplatesAPI.destroy(template.id);
      history.push(`/notification_templates`);
    }, [template.id, history])
  );

  const { error, dismissError } = useDismissableError(deleteError);

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
            <Detail
              label={i18n._(t`Recipient List`)}
              value={configuration.recipients} // array
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
            <Detail
              label={i18n._(t`Tags for the Annotation`)}
              value={configuration.annotation_tags} // array
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
            <Detail
              label={i18n._(t`Destination Channels or Users`)}
              value={configuration.targets} // array
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
              dataCy="nt-detail-pagerduty-rocketchat-username"
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
            <Detail
              label={i18n._(t`Destination Channels`)}
              value={configuration.channels} // array
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
            <Detail
              label={i18n._(t`Destination SMS Number`)}
              value={configuration.to_numbers} // array
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
            {/* <Detail
              label={i18n._(t`HTTP Headers`)}
              value={configuration.headers}
              dataCy="nt-detail-webhook-headers"
            /> */}
          </>
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

export default withI18n()(NotificationTemplateDetail);
