import React, { useEffect, useCallback, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { number, shape, bool } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import AlertModal from '../AlertModal';
import ErrorDetail from '../ErrorDetail';
import NotificationListItem from './NotificationListItem';
import PaginatedDataList from '../PaginatedDataList';
import { getQSConfig, parseQueryString } from '../../util/qs';
import useRequest from '../../util/useRequest';
import { NotificationTemplatesAPI } from '../../api';

const QS_CONFIG = getQSConfig('notification', {
  page: 1,
  page_size: 5,
  order_by: 'name',
});

function NotificationList({ apiModel, canToggleNotifications, id, i18n }) {
  const location = useLocation();
  const [isToggleLoading, setIsToggleLoading] = useState(false);
  const [toggleError, setToggleError] = useState(null);

  const {
    result: fetchNotificationsResult,
    result: {
      notifications,
      itemCount,
      startedTemplateIds,
      successTemplateIds,
      errorTemplateIds,
      typeLabels,
    },
    error: contentError,
    isLoading,
    request: fetchNotifications,
    setValue,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);
      const [
        {
          data: { results: notificationsResults, count: notificationsCount },
        },
        {
          data: { actions },
        },
      ] = await Promise.all([
        NotificationTemplatesAPI.read(params),
        NotificationTemplatesAPI.readOptions(),
      ]);

      const labels = actions.GET.notification_type.choices.reduce(
        (map, notifType) => ({ ...map, [notifType[0]]: notifType[1] }),
        {}
      );

      const idMatchParams =
        notificationsResults.length > 0
          ? { id__in: notificationsResults.map(n => n.id).join(',') }
          : {};

      const [
        { data: startedTemplates },
        { data: successTemplates },
        { data: errorTemplates },
      ] = await Promise.all([
        apiModel.readNotificationTemplatesStarted(id, idMatchParams),
        apiModel.readNotificationTemplatesSuccess(id, idMatchParams),
        apiModel.readNotificationTemplatesError(id, idMatchParams),
      ]);

      return {
        notifications: notificationsResults,
        itemCount: notificationsCount,
        startedTemplateIds: startedTemplates.results.map(st => st.id),
        successTemplateIds: successTemplates.results.map(su => su.id),
        errorTemplateIds: errorTemplates.results.map(e => e.id),
        typeLabels: labels,
      };
    }, [apiModel, id, location]),
    {
      notifications: [],
      itemCount: 0,
      startedTemplateIds: [],
      successTemplateIds: [],
      errorTemplateIds: [],
      typeLabels: {},
    }
  );

  useEffect(() => {
    fetchNotifications();
  }, [fetchNotifications]);

  const handleNotificationToggle = async (
    notificationId,
    isCurrentlyOn,
    status
  ) => {
    setIsToggleLoading(true);
    try {
      if (isCurrentlyOn) {
        await apiModel.disassociateNotificationTemplate(
          id,
          notificationId,
          status
        );
        setValue({
          ...fetchNotificationsResult,
          [`${status}TemplateIds`]: fetchNotificationsResult[
            `${status}TemplateIds`
          ].filter(i => i !== notificationId),
        });
      } else {
        await apiModel.associateNotificationTemplate(
          id,
          notificationId,
          status
        );
        setValue({
          ...fetchNotificationsResult,
          [`${status}TemplateIds`]: fetchNotificationsResult[
            `${status}TemplateIds`
          ].concat(notificationId),
        });
      }
    } catch (err) {
      setToggleError(err);
    } finally {
      setIsToggleLoading(false);
    }
  };

  return (
    <>
      <PaginatedDataList
        contentError={contentError}
        hasContentLoading={isLoading}
        items={notifications}
        itemCount={itemCount}
        pluralizedItemName={i18n._(t`Notifications`)}
        qsConfig={QS_CONFIG}
        toolbarSearchColumns={[
          {
            name: i18n._(t`Name`),
            key: 'name',
            isDefault: true,
          },
          {
            name: i18n._(t`Type`),
            key: 'type',
            options: [
              ['email', i18n._(t`Email`)],
              ['grafana', i18n._(t`Grafana`)],
              ['hipchat', i18n._(t`Hipchat`)],
              ['irc', i18n._(t`IRC`)],
              ['mattermost', i18n._(t`Mattermost`)],
              ['pagerduty', i18n._(t`Pagerduty`)],
              ['rocketchat', i18n._(t`Rocket.Chat`)],
              ['slack', i18n._(t`Slack`)],
              ['twilio', i18n._(t`Twilio`)],
              ['webhook', i18n._(t`Webhook`)],
            ],
          },
          {
            name: i18n._(t`Created by (username)`),
            key: 'created_by__username',
          },
          {
            name: i18n._(t`Modified by (username)`),
            key: 'modified_by__username',
          },
        ]}
        toolbarSortColumns={[
          {
            name: i18n._(t`Name`),
            key: 'name',
          },
        ]}
        renderItem={notification => (
          <NotificationListItem
            key={notification.id}
            notification={notification}
            detailUrl={`/notifications/${notification.id}`}
            canToggleNotifications={canToggleNotifications && !isToggleLoading}
            toggleNotification={handleNotificationToggle}
            errorTurnedOn={errorTemplateIds.includes(notification.id)}
            startedTurnedOn={startedTemplateIds.includes(notification.id)}
            successTurnedOn={successTemplateIds.includes(notification.id)}
            typeLabels={typeLabels}
          />
        )}
      />
      {toggleError && (
        <AlertModal
          variant="error"
          title={i18n._(t`Error!`)}
          isOpen={!isToggleLoading}
          onClose={() => setToggleError(null)}
        >
          {i18n._(t`Failed to toggle notification.`)}
          <ErrorDetail error={toggleError} />
        </AlertModal>
      )}
    </>
  );
}

NotificationList.propTypes = {
  apiModel: shape({}).isRequired,
  id: number.isRequired,
  canToggleNotifications: bool.isRequired,
};

export default withI18n()(NotificationList);
