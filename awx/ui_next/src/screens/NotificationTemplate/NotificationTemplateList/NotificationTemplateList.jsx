import React, { useCallback, useEffect } from 'react';
import { useLocation, useRouteMatch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Card, PageSection } from '@patternfly/react-core';
import { NotificationTemplatesAPI } from '../../../api';
import PaginatedDataList, {
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

function NotificationTemplatesList({ i18n }) {
  const location = useLocation();
  const match = useRouteMatch();

  const addUrl = `${match.url}/add`;

  const {
    result: { templates, count, actions },
    error: contentError,
    isLoading: isTemplatesLoading,
    request: fetchTemplates,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);
      const responses = await Promise.all([
        NotificationTemplatesAPI.read(params),
        NotificationTemplatesAPI.readOptions(),
      ]);
      return {
        templates: responses[0].data.results,
        count: responses[0].data.count,
        actions: responses[1].data.actions,
      };
    }, [location]),
    {
      templates: [],
      count: 0,
      actions: {},
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
    useCallback(async () => {
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

  const canAdd = actions && actions.POST;

  return (
    <>
      <PageSection>
        <Card>
          <PaginatedDataList
            contentError={contentError}
            hasContentLoading={isTemplatesLoading || isDeleteLoading}
            items={templates}
            itemCount={count}
            pluralizedItemName={i18n._(t`Notification Templates`)}
            qsConfig={QS_CONFIG}
            onRowClick={handleSelect}
            toolbarSearchColumns={[
              {
                name: i18n._(t`Name`),
                key: 'name',
                isDefault: true,
              },
              {
                name: i18n._(t`Description`),
                key: 'description__icontains',
              },
              {
                name: i18n._(t`Type`),
                key: 'notification_type',
              },
            ]}
            toolbarSortColumns={[
              {
                name: i18n._(t`Name`),
                key: 'name',
              },
              {
                name: i18n._(t`Type`),
                key: 'notification_type',
              },
            ]}
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
                    pluralizedItemName="Organizations"
                  />,
                ]}
              />
            )}
            renderItem={template => (
              <NotificationTemplateListItem
                key={template.id}
                template={template}
                detailUrl={`${match.url}/${template.id}`}
                isSelected={selected.some(row => row.id === template.id)}
                onSelect={() => handleSelect(template)}
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
        title={i18n._(t`Error!`)}
        onClose={clearDeletionError}
      >
        {i18n._(t`Failed to delete one or more organizations.`)}
        <ErrorDetail error={deletionError} />
      </AlertModal>
    </>
  );
}

export default withI18n()(NotificationTemplatesList);
