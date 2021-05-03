import React, { useCallback, useEffect, useState } from 'react';
import { useLocation, useRouteMatch } from 'react-router-dom';

import { t } from '@lingui/macro';
import {
  Alert,
  AlertActionCloseButton,
  AlertGroup,
  Card,
  PageSection,
} from '@patternfly/react-core';
import { NotificationTemplatesAPI } from '../../../api';
import PaginatedTable, {
  HeaderRow,
  HeaderCell,
} from '../../../components/PaginatedTable';
import {
  ToolbarAddButton,
  ToolbarDeleteButton,
} from '../../../components/PaginatedDataList';
import AlertModal from '../../../components/AlertModal';
import ErrorDetail from '../../../components/ErrorDetail';
import DataListToolbar from '../../../components/DataListToolbar';
import NotificationTemplateListItem from './NotificationTemplateListItem';
import useRequest, { useDeleteItems } from '../../../util/useRequest';
import useSelected from '../../../util/useSelected';
import { getQSConfig, parseQueryString } from '../../../util/qs';

const QS_CONFIG = getQSConfig('notification-templates', {
  page: 1,
  page_size: 20,
  order_by: 'name',
});

function NotificationTemplatesList() {
  const location = useLocation();
  const match = useRouteMatch();
  const [testToasts, setTestToasts] = useState([]);

  const addUrl = `${match.url}/add`;

  const {
    result: {
      templates,
      count,
      actions,
      relatedSearchableKeys,
      searchableKeys,
    },
    error: contentError,
    isLoading: isTemplatesLoading,
    request: fetchTemplates,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);
      const [response, actionsResponse] = await Promise.all([
        NotificationTemplatesAPI.read(params),
        NotificationTemplatesAPI.readOptions(),
      ]);
      return {
        templates: response.data.results,
        count: response.data.count,
        actions: actionsResponse.data.actions,
        relatedSearchableKeys: (
          actionsResponse.data?.related_search_fields || []
        ).map(val => val.slice(0, -8)),
        searchableKeys: Object.keys(
          actionsResponse.data.actions?.GET || {}
        ).filter(key => actionsResponse.data.actions?.GET[key].filterable),
      };
    }, [location]),
    {
      templates: [],
      count: 0,
      actions: {},
      relatedSearchableKeys: [],
      searchableKeys: [],
    }
  );

  useEffect(() => {
    fetchTemplates();
  }, [fetchTemplates]);

  const { selected, isAllSelected, handleSelect, setSelected } = useSelected(
    templates
  );

  const {
    isLoading: isDeleteLoading,
    deleteItems: deleteTemplates,
    deletionError,
    clearDeletionError,
  } = useDeleteItems(
    useCallback(() => {
      return Promise.all(
        selected.map(({ id }) => NotificationTemplatesAPI.destroy(id))
      );
    }, [selected]),
    {
      qsConfig: QS_CONFIG,
      allItemsSelected: isAllSelected,
      fetchItems: fetchTemplates,
    }
  );

  const handleDelete = async () => {
    await deleteTemplates();
    setSelected([]);
  };

  const addTestToast = useCallback(notification => {
    setTestToasts(oldToasts => [...oldToasts, notification]);
  }, []);

  const removeTestToast = notificationId => {
    setTestToasts(oldToasts =>
      oldToasts.filter(toast => toast.id !== notificationId)
    );
  };

  const canAdd = actions && actions.POST;
  const alertGroupDataCy = 'notification-template-alerts';

  return (
    <>
      <PageSection>
        <Card>
          <PaginatedTable
            contentError={contentError}
            hasContentLoading={isTemplatesLoading || isDeleteLoading}
            items={templates}
            itemCount={count}
            pluralizedItemName={t`Notification Templates`}
            qsConfig={QS_CONFIG}
            onRowClick={handleSelect}
            toolbarSearchColumns={[
              {
                name: t`Name`,
                key: 'name',
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
                name: t`Created by (username)`,
                key: 'created_by__username__icontains',
              },
              {
                name: t`Modified by (username)`,
                key: 'modified_by__username__icontains',
              },
            ]}
            toolbarSearchableKeys={searchableKeys}
            toolbarRelatedSearchableKeys={relatedSearchableKeys}
            renderToolbar={props => (
              <DataListToolbar
                {...props}
                showSelectAll
                isAllSelected={isAllSelected}
                onSelectAll={set => setSelected(set ? [...templates] : [])}
                qsConfig={QS_CONFIG}
                additionalControls={[
                  ...(canAdd
                    ? [<ToolbarAddButton key="add" linkTo={addUrl} />]
                    : []),
                  <ToolbarDeleteButton
                    key="delete"
                    onDelete={handleDelete}
                    itemsToDelete={selected}
                    pluralizedItemName={t`Notification Templates`}
                  />,
                ]}
              />
            )}
            headerRow={
              <HeaderRow qsConfig={QS_CONFIG}>
                <HeaderCell sortKey="name">{t`Name`}</HeaderCell>
                <HeaderCell>{t`Status`}</HeaderCell>
                <HeaderCell sortKey="notification_type">{t`Type`}</HeaderCell>
                <HeaderCell>{t`Actions`}</HeaderCell>
              </HeaderRow>
            }
            renderRow={(template, index) => (
              <NotificationTemplateListItem
                onAddToast={addTestToast}
                key={template.id}
                fetchTemplates={fetchTemplates}
                template={template}
                detailUrl={`${match.url}/${template.id}`}
                isSelected={selected.some(row => row.id === template.id)}
                onSelect={() => handleSelect(template)}
                rowIndex={index}
              />
            )}
            emptyStateControls={
              canAdd ? <ToolbarAddButton key="add" linkTo={addUrl} /> : null
            }
          />
        </Card>
      </PageSection>
      <AlertModal
        isOpen={deletionError}
        variant="error"
        title={t`Error!`}
        onClose={clearDeletionError}
      >
        {t`Failed to delete one or more notification template.`}
        <ErrorDetail error={deletionError} />
      </AlertModal>
      <AlertGroup data-cy={alertGroupDataCy} isToast>
        {testToasts
          .filter(notification => notification.status !== 'pending')
          .map(notification => (
            <Alert
              actionClose={
                <AlertActionCloseButton
                  onClose={() => removeTestToast(notification.id)}
                />
              }
              onTimeout={() => removeTestToast(notification.id)}
              timeout={notification.status !== 'failed'}
              title={notification.summary_fields.notification_template.name}
              variant={notification.status === 'failed' ? 'danger' : 'success'}
              key={`notification-template-alert-${notification.id}`}
              ouiaId={`notification-template-alert-${notification.id}`}
            >
              <>
                {notification.status === 'successful' && (
                  <p>{t`Notification sent successfully`}</p>
                )}
                {notification.status === 'failed' &&
                  notification?.error === 'timed out' && (
                    <p>{t`Notification timed out`}</p>
                  )}
                {notification.status === 'failed' &&
                  notification?.error !== 'timed out' && (
                    <p>{notification.error}</p>
                  )}
              </>
            </Alert>
          ))}
      </AlertGroup>
    </>
  );
}

export default NotificationTemplatesList;
