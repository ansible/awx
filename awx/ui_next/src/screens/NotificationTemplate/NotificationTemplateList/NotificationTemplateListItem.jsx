import 'styled-components/macro';
import React, { useState, useEffect, useCallback } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Link } from 'react-router-dom';
import styled from 'styled-components';
import {
  Button,
  DataListAction as _DataListAction,
  DataListCheck,
  DataListItem,
  DataListItemCells,
  DataListItemRow,
  Tooltip,
} from '@patternfly/react-core';
import { PencilAltIcon, BellIcon } from '@patternfly/react-icons';
import { NotificationTemplatesAPI, NotificationsAPI } from '../../../api';
import DataListCell from '../../../components/DataListCell';
import StatusLabel from '../../../components/StatusLabel';
import useRequest from '../../../util/useRequest';
import { NOTIFICATION_TYPES } from '../constants';

const DataListAction = styled(_DataListAction)`
  align-items: center;
  display: grid;
  grid-gap: 16px;
  grid-template-columns: 40px 40px;
`;

const NUM_RETRIES = 25;
const RETRY_TIMEOUT = 5000;

function NotificationTemplateListItem({
  template,
  detailUrl,
  isSelected,
  onSelect,
  i18n,
}) {
  const recentNotifications = template.summary_fields?.recent_notifications;
  const latestStatus = recentNotifications
    ? recentNotifications[0]?.status
    : null;
  const [status, setStatus] = useState(latestStatus);

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
    <DataListItem key={template.id} aria-labelledby={labelId} id={template.id}>
      <DataListItemRow>
        <DataListCheck
          id={`select-template-${template.id}`}
          checked={isSelected}
          onChange={onSelect}
          aria-labelledby={labelId}
        />
        <DataListItemCells
          dataListCells={[
            <DataListCell key="name" id={labelId}>
              <Link to={detailUrl}>
                <b>{template.name}</b>
              </Link>
            </DataListCell>,
            <DataListCell key="status">
              {status && <StatusLabel status={status} />}
            </DataListCell>,
            <DataListCell key="type">
              <strong>{i18n._(t`Type:`)}</strong>{' '}
              {NOTIFICATION_TYPES[template.notification_type] ||
                template.notification_type}
            </DataListCell>,
          ]}
        />
        <DataListAction aria-label="actions" aria-labelledby={labelId}>
          <Tooltip content={i18n._(t`Test Notification`)} position="top">
            <Button
              aria-label={i18n._(t`Test Notification`)}
              variant="plain"
              onClick={sendTestNotification}
              disabled={isLoading}
            >
              <BellIcon />
            </Button>
          </Tooltip>
          {template.summary_fields.user_capabilities.edit ? (
            <Tooltip
              content={i18n._(t`Edit Notification Template`)}
              position="top"
            >
              <Button
                aria-label={i18n._(t`Edit Notification Template`)}
                variant="plain"
                component={Link}
                to={`/notification_templates/${template.id}/edit`}
              >
                <PencilAltIcon />
              </Button>
            </Tooltip>
          ) : (
            <div />
          )}
        </DataListAction>
      </DataListItemRow>
    </DataListItem>
  );
}

export default withI18n()(NotificationTemplateListItem);
