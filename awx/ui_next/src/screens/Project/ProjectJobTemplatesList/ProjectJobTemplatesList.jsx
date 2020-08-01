import React, { useCallback, useEffect } from 'react';
import { useLocation, useParams } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Card } from '@patternfly/react-core';
import { JobTemplatesAPI } from '../../../api';
import AlertModal from '../../../components/AlertModal';
import DatalistToolbar from '../../../components/DataListToolbar';
import ErrorDetail from '../../../components/ErrorDetail';
import PaginatedDataList, {
  ToolbarAddButton,
  ToolbarDeleteButton,
} from '../../../components/PaginatedDataList';
import { getQSConfig, parseQueryString } from '../../../util/qs';
import useSelected from '../../../util/useSelected';
import useRequest, { useDeleteItems } from '../../../util/useRequest';
import ProjectTemplatesListItem from './ProjectJobTemplatesListItem';

const QS_CONFIG = getQSConfig('template', {
  page: 1,
  page_size: 20,
  order_by: 'name',
});

function ProjectJobTemplatesList({ i18n }) {
  const { id: projectId } = useParams();
  const location = useLocation();

  const {
    result: { jobTemplates, itemCount, actions },
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
      };
    }, [location, projectId]),
    {
      jobTemplates: [],
      itemCount: 0,
      actions: {},
    }
  );

  useEffect(() => {
    fetchTemplates();
  }, [fetchTemplates]);

  const { selected, isAllSelected, handleSelect, setSelected } = useSelected(
    jobTemplates
  );

  const {
    isLoading: isDeleteLoading,
    deleteItems: deleteTemplates,
    deletionError,
    clearDeletionError,
  } = useDeleteItems(
    useCallback(async () => {
      return Promise.all(
        selected.map(template => JobTemplatesAPI.destroy(template.id))
      );
    }, [selected]),
    {
      qsConfig: QS_CONFIG,
      allItemsSelected: isAllSelected,
      fetchItems: fetchTemplates,
    }
  );

  const handleTemplateDelete = async () => {
    await deleteTemplates();
    setSelected([]);
  };

  const canAddJT =
    actions && Object.prototype.hasOwnProperty.call(actions, 'POST');

  const addButton = (
    <ToolbarAddButton key="add" linkTo="/templates/job_template/add/" />
  );

  return (
    <>
      <Card>
        <PaginatedDataList
          contentError={contentError}
          hasContentLoading={isDeleteLoading || isLoading}
          items={jobTemplates}
          itemCount={itemCount}
          pluralizedItemName={i18n._(t`Job templates`)}
          qsConfig={QS_CONFIG}
          onRowClick={handleSelect}
          toolbarSearchColumns={[
            {
              name: i18n._(t`Name`),
              key: 'name',
              isDefault: true,
            },
            {
              name: i18n._(t`Playbook name`),
              key: 'job_template__playbook',
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
              name: i18n._(t`Inventory`),
              key: 'job_template__inventory__id',
            },
            {
              name: i18n._(t`Last job run`),
              key: 'last_job_run',
            },
            {
              name: i18n._(t`Modified`),
              key: 'modified',
            },
            {
              name: i18n._(t`Name`),
              key: 'name',
            },
            {
              name: i18n._(t`Project`),
              key: 'jobtemplate__project__id',
            },
            {
              name: i18n._(t`Type`),
              key: 'type',
            },
          ]}
          renderToolbar={props => (
            <DatalistToolbar
              {...props}
              showSelectAll
              showExpandCollapse
              isAllSelected={isAllSelected}
              onSelectAll={isSelected =>
                setSelected(isSelected ? [...jobTemplates] : [])
              }
              qsConfig={QS_CONFIG}
              additionalControls={[
                ...(canAddJT ? [addButton] : []),
                <ToolbarDeleteButton
                  key="delete"
                  onDelete={handleTemplateDelete}
                  itemsToDelete={selected}
                  pluralizedItemName={i18n._(t`Job templates`)}
                />,
              ]}
            />
          )}
          renderItem={template => (
            <ProjectTemplatesListItem
              key={template.id}
              value={template.name}
              template={template}
              detailUrl={`/templates/${template.type}/${template.id}/details`}
              onSelect={() => handleSelect(template)}
              isSelected={selected.some(row => row.id === template.id)}
            />
          )}
          emptyStateControls={canAddJT && addButton}
        />
      </Card>
      <AlertModal
        isOpen={deletionError}
        variant="danger"
        title={i18n._(t`Error!`)}
        onClose={clearDeletionError}
      >
        {i18n._(t`Failed to delete one or more job templates.`)}
        <ErrorDetail error={deletionError} />
      </AlertModal>
    </>
  );
}

export default withI18n()(ProjectJobTemplatesList);
