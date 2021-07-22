import React, { useCallback, useEffect } from 'react';
import { useLocation, useParams } from 'react-router-dom';

import { t } from '@lingui/macro';
import { Card } from '@patternfly/react-core';
import { JobTemplatesAPI } from 'api';
import AlertModal from 'components/AlertModal';
import DatalistToolbar from 'components/DataListToolbar';
import ErrorDetail from 'components/ErrorDetail';
import PaginatedTable, {
  HeaderRow,
  HeaderCell,
  ToolbarAddButton,
  ToolbarDeleteButton,
} from 'components/PaginatedTable';
import { getQSConfig, parseQueryString } from 'util/qs';
import useSelected from 'hooks/useSelected';
import useRequest, { useDeleteItems } from 'hooks/useRequest';
import ProjectTemplatesListItem from './ProjectJobTemplatesListItem';

const QS_CONFIG = getQSConfig('template', {
  page: 1,
  page_size: 20,
  order_by: 'name',
});

function ProjectJobTemplatesList() {
  const { id: projectId } = useParams();
  const location = useLocation();

  const {
    result: {
      jobTemplates,
      itemCount,
      actions,
      relatedSearchableKeys,
      searchableKeys,
    },
    error: contentError,
    isLoading,
    request: fetchTemplates,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);
      params.project = projectId;
      const [response, actionsResponse] = await Promise.all([
        JobTemplatesAPI.read(params),
        JobTemplatesAPI.readOptions(),
      ]);
      return {
        jobTemplates: response.data.results,
        itemCount: response.data.count,
        actions: actionsResponse.data.actions,
        relatedSearchableKeys: (
          actionsResponse?.data?.related_search_fields || []
        ).map((val) => val.slice(0, -8)),
        searchableKeys: Object.keys(
          actionsResponse.data.actions?.GET || {}
        ).filter((key) => actionsResponse.data.actions?.GET[key].filterable),
      };
    }, [location, projectId]),
    {
      jobTemplates: [],
      itemCount: 0,
      actions: {},
      relatedSearchableKeys: [],
      searchableKeys: [],
    }
  );

  useEffect(() => {
    fetchTemplates();
  }, [fetchTemplates]);

  const { selected, isAllSelected, handleSelect, clearSelected, selectAll } =
    useSelected(jobTemplates);

  const {
    isLoading: isDeleteLoading,
    deleteItems: deleteTemplates,
    deletionError,
    clearDeletionError,
  } = useDeleteItems(
    useCallback(
      () =>
        Promise.all(
          selected.map((template) => JobTemplatesAPI.destroy(template.id))
        ),
      [selected]
    ),
    {
      qsConfig: QS_CONFIG,
      allItemsSelected: isAllSelected,
      fetchItems: fetchTemplates,
    }
  );

  const handleTemplateDelete = async () => {
    await deleteTemplates();
    clearSelected();
  };

  const canAddJT =
    actions && Object.prototype.hasOwnProperty.call(actions, 'POST');

  const addButton = (
    <ToolbarAddButton key="add" linkTo="/templates/job_template/add/" />
  );

  return (
    <>
      <Card>
        <PaginatedTable
          contentError={contentError}
          hasContentLoading={isDeleteLoading || isLoading}
          items={jobTemplates}
          itemCount={itemCount}
          pluralizedItemName={t`Job templates`}
          qsConfig={QS_CONFIG}
          clearSelected={clearSelected}
          toolbarSearchColumns={[
            {
              name: t`Name`,
              key: 'name__icontains',
              isDefault: true,
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
          renderToolbar={(props) => (
            <DatalistToolbar
              {...props}
              isAllSelected={isAllSelected}
              onSelectAll={selectAll}
              qsConfig={QS_CONFIG}
              additionalControls={[
                ...(canAddJT ? [addButton] : []),
                <ToolbarDeleteButton
                  key="delete"
                  onDelete={handleTemplateDelete}
                  itemsToDelete={selected}
                  pluralizedItemName={t`Job templates`}
                />,
              ]}
            />
          )}
          headerRow={
            <HeaderRow qsConfig={QS_CONFIG}>
              <HeaderCell sortKey="name">{t`Name`}</HeaderCell>
              <HeaderCell sortKey="type">{t`Type`}</HeaderCell>
              <HeaderCell>{t`Recent jobs`}</HeaderCell>
              <HeaderCell>{t`Actions`}</HeaderCell>
            </HeaderRow>
          }
          renderRow={(template, index) => (
            <ProjectTemplatesListItem
              key={template.id}
              value={template.name}
              template={template}
              detailUrl={`/templates/${template.type}/${template.id}/details`}
              onSelect={() => handleSelect(template)}
              isSelected={selected.some((row) => row.id === template.id)}
              rowIndex={index}
            />
          )}
          emptyStateControls={canAddJT && addButton}
        />
      </Card>
      <AlertModal
        isOpen={deletionError}
        variant="danger"
        title={t`Error!`}
        onClose={clearDeletionError}
      >
        {t`Failed to delete one or more job templates.`}
        <ErrorDetail error={deletionError} />
      </AlertModal>
    </>
  );
}

export default ProjectJobTemplatesList;
