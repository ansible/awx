import 'styled-components/macro';
import React, { useState, useEffect, useCallback } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Link } from 'react-router-dom';
import { Button } from '@patternfly/react-core';
import { Tr, Td } from '@patternfly/react-table';
import { PencilAltIcon, BellIcon } from '@patternfly/react-icons';
import { ActionsTd, ActionItem } from '../../../components/PaginatedTable';
import { timeOfDay } from '../../../util/dates';
import { NotificationTemplatesAPI, NotificationsAPI } from '../../../api';
import StatusLabel from '../../../components/StatusLabel';
import CopyButton from '../../../components/CopyButton';
import useRequest from '../../../util/useRequest';
import { NOTIFICATION_TYPES } from '../constants';

const NUM_RETRIES = 25;
const RETRY_TIMEOUT = 5000;

function NotificationTemplateListItem({
  template,
  detailUrl,
  fetchTemplates,
  isSelected,
  onSelect,
  rowIndex,
  i18n,
}) {
  const recentNotifications = template.summary_fields?.recent_notifications;
  const latestStatus = recentNotifications
    ? recentNotifications[0]?.status
    : null;
  const [status, setStatus] = useState(latestStatus);
  const [isCopyDisabled, setIsCopyDisabled] = useState(false);

  const copyTemplate = useCallback(async () => {
    await NotificationTemplatesAPI.copy(template.id, {
      name: `${template.name} @ ${timeOfDay()}`,
    });
    await fetchTemplates();
  }, [template.id, template.name, fetchTemplates]);

  const handleCopyStart = useCallback(() => {
    setIsCopyDisabled(true);
  }, []);

  const handleCopyFinish = useCallback(() => {
    setIsCopyDisabled(false);
  }, []);

  useEffect(() => {
    setStatus(latestStatus);
  }, [latestStatus]);

  const { request: sendTestNotification, isLoading, error } = useRequest(
    useCallback(async () => {
      const request = NotificationTemplatesAPI.test(template.id);
      setStatus('running');
      let retries = NUM_RETRIES;
      const {
        data: { notification: notificationId },
      } = await request;

      async function pollForStatusChange() {
        const { data: notification } = await NotificationsAPI.readDetail(
          notificationId
        );
        if (notification.status !== 'pending') {
          setStatus(notification.status);
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

  useEffect(() => {
    if (error) {
      setStatus('error');
    }
  }, [error]);

  const labelId = `template-name-${template.id}`;

  return (
    <Tr id={`notification-template-row-${template.id}`}>
      <Td
        select={{
          rowIndex,
          isSelected,
          onSelect,
        }}
        dataLabel={i18n._(t`Selected`)}
      />
      <Td id={labelId} dataLabel={i18n._(t`Name`)}>
        <Link to={`${detailUrl}`}>
          <b>{template.name}</b>
        </Link>
      </Td>
      <Td dataLabel={i18n._(t`Status`)}>
        {status && <StatusLabel status={status} />}
      </Td>
      <Td dataLabel={i18n._(t`Type`)}>
        {NOTIFICATION_TYPES[template.notification_type] ||
          template.notification_type}
      </Td>
      <ActionsTd dataLabel={i18n._(t`Actions`)}>
        <ActionItem visible tooltip={i18n._(t`Test notification`)}>
          <Button
            aria-label={i18n._(t`Test Notification`)}
            variant="plain"
            onClick={sendTestNotification}
            isDisabled={isLoading || status === 'running'}
          >
            <BellIcon />
          </Button>
        </ActionItem>
        <ActionItem
          visible={template.summary_fields.user_capabilities.edit}
          tooltip={i18n._(t`Edit`)}
        >
          <Button
            aria-label={i18n._(t`Edit Notification Template`)}
            variant="plain"
            component={Link}
            to={`/notification_templates/${template.id}/edit`}
          >
            <PencilAltIcon />
          </Button>
        </ActionItem>
        <ActionItem
          visible={template.summary_fields.user_capabilities.copy}
          tooltip={i18n._(t`Copy Notification Template`)}
        >
          <CopyButton
            copyItem={copyTemplate}
            isCopyDisabled={isCopyDisabled}
            onCopyStart={handleCopyStart}
            onCopyFinish={handleCopyFinish}
            errorMessage={i18n._(t`Failed to copy template.`)}
          />
        </ActionItem>
      </ActionsTd>
    </Tr>
  );
}

export default withI18n()(NotificationTemplateListItem);
