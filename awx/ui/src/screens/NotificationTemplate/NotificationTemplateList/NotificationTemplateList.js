import React, { useCallback, useEffect } from 'react';
import { useLocation, useRouteMatch } from 'react-router-dom';

import { t } from '@lingui/macro';
import { Card, PageSection } from '@patternfly/react-core';
import { NotificationTemplatesAPI } from 'api';
import PaginatedTable, {
  HeaderRow,
  HeaderCell,
  ToolbarAddButton,
  ToolbarDeleteButton,
  getSearchableKeys,
} from 'components/PaginatedTable';
import AlertModal from 'components/AlertModal';
import ErrorDetail from 'components/ErrorDetail';
import DataListToolbar from 'components/DataListToolbar';
import useRequest, { useDeleteItems } from 'hooks/useRequest';
import useSelected from 'hooks/useSelected';
import useToast, { AlertVariant } from 'hooks/useToast';
import { getQSConfig, parseQueryString } from 'util/qs';
import NotificationTemplateListItem from './NotificationTemplateListItem';

const QS_CONFIG = getQSConfig('notification-templates', {
  page: 1,
  page_size: 20,
  order_by: 'name',
});

function NotificationTemplatesList() {
  const location = useLocation();
  const match = useRouteMatch();
  // const [testToasts, setTestToasts] = useState([]);
  const { addToast, Toast, toastProps } = useToast();

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
        ).map((val) => val.slice(0, -8)),
        searchableKeys: getSearchableKeys(actionsResponse.data.actions?.GET),
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

  const { selected, isAllSelected, handleSelect, clearSelected, selectAll } =
    useSelected(templates);

  const {
    isLoading: isDeleteLoading,
    deleteItems: deleteTemplates,
    deletionError,
    clearDeletionError,
  } = useDeleteItems(
    useCallback(
      () =>
        Promise.all(
          selected.map(({ id }) => NotificationTemplatesAPI.destroy(id))
        ),
      [selected]
    ),
    {
      qsConfig: QS_CONFIG,
      allItemsSelected: isAllSelected,
      fetchItems: fetchTemplates,
    }
  );

  const handleDelete = async () => {
    await deleteTemplates();
    clearSelected();
  };

  const canAdd = actions && actions.POST;

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
            clearSelected={clearSelected}
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
            renderToolbar={(props) => (
              <DataListToolbar
                {...props}
                isAllSelected={isAllSelected}
                onSelectAll={selectAll}
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
                <HeaderCell sortKey="organization">{t`Organization`}</HeaderCell>
                <HeaderCell>{t`Actions`}</HeaderCell>
              </HeaderRow>
            }
            renderRow={(template, index) => (
              <NotificationTemplateListItem
                onAddToast={(notification) => {
                  if (notification.status === 'pending') {
                    return;
                  }

                  let message;
                  if (notification.status === 'successful') {
                    message = t`Notification sent successfully`;
                  }
                  if (notification.status === 'failed') {
                    if (notification?.error === 'timed out') {
                      message = t`Notification timed out`;
                    } else {
                      message = notification.error;
                    }
                  }

                  addToast({
                    id: notification.id,
                    title:
                      notification.summary_fields.notification_template.name,
                    variant:
                      notification.status === 'failed'
                        ? AlertVariant.danger
                        : AlertVariant.success,
                    hasTimeout: notification.status !== 'failed',
                    message,
                  });
                }}
                key={template.id}
                fetchTemplates={fetchTemplates}
                template={template}
                detailUrl={`${match.url}/${template.id}`}
                isSelected={selected.some((row) => row.id === template.id)}
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
      <Toast {...toastProps} />
    </>
  );
}

export default NotificationTemplatesList;
