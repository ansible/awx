import React, { useEffect, useCallback, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { number, shape, bool } from 'prop-types';

import { t } from '@lingui/macro';
import { getQSConfig, parseQueryString } from 'util/qs';
import useRequest from 'hooks/useRequest';
import { NotificationTemplatesAPI } from 'api';
import AlertModal from '../AlertModal';
import ErrorDetail from '../ErrorDetail';
import NotificationListItem from './NotificationListItem';
import PaginatedTable, {
  HeaderRow,
  HeaderCell,
  getSearchableKeys,
} from '../PaginatedTable';

const QS_CONFIG = getQSConfig('notification', {
  page: 1,
  page_size: 5,
  order_by: 'name',
});

function NotificationList({
  apiModel,
  canToggleNotifications,
  id,

  showApprovalsToggle,
}) {
  const location = useLocation();
  const [loadingToggleIds, setLoadingToggleIds] = useState([]);
  const [toggleError, setToggleError] = useState(null);

  const {
    result: fetchNotificationsResults,
    result: {
      notifications,
      itemCount,
      approvalsTemplateIds,
      startedTemplateIds,
      successTemplateIds,
      errorTemplateIds,
      typeLabels,
      relatedSearchableKeys,
      searchableKeys,
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
        actionsResponse,
      ] = await Promise.all([
        NotificationTemplatesAPI.read(params),
        NotificationTemplatesAPI.readOptions(),
      ]);

      const labels =
        actionsResponse.data.actions.GET.notification_type.choices.reduce(
          (map, notifType) => ({ ...map, [notifType[0]]: notifType[1] }),
          {}
        );

      const idMatchParams =
        notificationsResults.length > 0
          ? { id__in: notificationsResults.map((n) => n.id).join(',') }
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

      const rtnObj = {
        notifications: notificationsResults,
        itemCount: notificationsCount,
        startedTemplateIds: startedTemplates.results.map((st) => st.id),
        successTemplateIds: successTemplates.results.map((su) => su.id),
        errorTemplateIds: errorTemplates.results.map((e) => e.id),
        typeLabels: labels,
        relatedSearchableKeys: (
          actionsResponse?.data?.related_search_fields || []
        ).map((val) => val.slice(0, -8)),
        searchableKeys: getSearchableKeys(actionsResponse.data.actions?.GET),
      };

      if (showApprovalsToggle) {
        const { data: approvalsTemplates } =
          await apiModel.readNotificationTemplatesApprovals(id, idMatchParams);
        rtnObj.approvalsTemplateIds = approvalsTemplates.results.map(
          (st) => st.id
        );
      } else {
        rtnObj.approvalsTemplateIds = [];
      }

      return rtnObj;
    }, [apiModel, id, location, showApprovalsToggle]),
    {
      notifications: [],
      itemCount: 0,
      approvalsTemplateIds: [],
      startedTemplateIds: [],
      successTemplateIds: [],
      errorTemplateIds: [],
      typeLabels: {},
      relatedSearchableKeys: [],
      searchableKeys: [],
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
    setLoadingToggleIds(loadingToggleIds.concat([notificationId]));
    try {
      if (isCurrentlyOn) {
        await apiModel.disassociateNotificationTemplate(
          id,
          notificationId,
          status
        );
        setValue({
          ...fetchNotificationsResults,
          [`${status}TemplateIds`]: fetchNotificationsResults[
            `${status}TemplateIds`
          ].filter((i) => i !== notificationId),
        });
      } else {
        await apiModel.associateNotificationTemplate(
          id,
          notificationId,
          status
        );
        setValue({
          ...fetchNotificationsResults,
          [`${status}TemplateIds`]:
            fetchNotificationsResults[`${status}TemplateIds`].concat(
              notificationId
            ),
        });
      }
    } catch (err) {
      setToggleError(err);
    } finally {
      setLoadingToggleIds(
        loadingToggleIds.filter((item) => item !== notificationId)
      );
    }
  };

  return (
    <>
      <PaginatedTable
        contentError={contentError}
        hasContentLoading={isLoading}
        items={notifications}
        itemCount={itemCount}
        pluralizedItemName={t`Notifications`}
        qsConfig={QS_CONFIG}
        toolbarSearchColumns={[
          {
            name: t`Name`,
            key: 'name__icontains',
            isDefault: true,
          },
          {
            name: t`Description`,
            key: 'description__icontains',
          },
          {
            name: t`Notification type`,
            key: 'or__notification_type',
            options: [
              ['email', t`Email`],
              ['grafana', t`Grafana`],
              ['hipchat', t`Hipchat`],
              ['irc', t`IRC`],
              ['mattermost', t`Mattermost`],
              ['pagerduty', t`Pagerduty`],
              ['rocketchat', t`Rocket.Chat`],
              ['slack', t`Slack`],
              ['twilio', t`Twilio`],
              ['webhook', t`Webhook`],
            ],
          },
          {
            name: t`Created By (Username)`,
            key: 'created_by__username__icontains',
          },
          {
            name: t`Modified By (Username)`,
            key: 'modified_by__username__icontains',
          },
        ]}
        toolbarSearchableKeys={searchableKeys}
        toolbarRelatedSearchableKeys={relatedSearchableKeys}
        headerRow={
          <HeaderRow qsConfig={QS_CONFIG} isSelectable={false}>
            <HeaderCell sortKey="name">{t`Name`}</HeaderCell>
            <HeaderCell sortKey="notification_type">{t`Type`}</HeaderCell>
            <HeaderCell>{t`Options`}</HeaderCell>
          </HeaderRow>
        }
        renderRow={(notification, index) => (
          <NotificationListItem
            key={notification.id}
            notification={notification}
            detailUrl={`/notification_templates/${notification.id}/details`}
            canToggleNotifications={
              canToggleNotifications &&
              !loadingToggleIds.includes(notification.id)
            }
            toggleNotification={handleNotificationToggle}
            approvalsTurnedOn={approvalsTemplateIds.includes(notification.id)}
            errorTurnedOn={errorTemplateIds.includes(notification.id)}
            startedTurnedOn={startedTemplateIds.includes(notification.id)}
            successTurnedOn={successTemplateIds.includes(notification.id)}
            typeLabels={typeLabels}
            showApprovalsToggle={showApprovalsToggle}
            rowIndex={index}
          />
        )}
      />
      {toggleError && (
        <AlertModal
          variant="error"
          title={t`Error!`}
          isOpen={loadingToggleIds.length === 0}
          onClose={() => setToggleError(null)}
        >
          {t`Failed to toggle notification.`}
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
  showApprovalsToggle: bool,
};

NotificationList.defaultProps = {
  showApprovalsToggle: false,
};

export default NotificationList;
