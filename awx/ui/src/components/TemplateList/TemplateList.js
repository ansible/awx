import React, { useEffect, useCallback } from 'react';
import { useLocation, Link } from 'react-router-dom';
import { t, Plural } from '@lingui/macro';
import { Card, DropdownItem } from '@patternfly/react-core';
import {
  JobTemplatesAPI,
  UnifiedJobTemplatesAPI,
  WorkflowJobTemplatesAPI,
} from 'api';
import useRequest, { useDeleteItems } from 'hooks/useRequest';
import useSelected from 'hooks/useSelected';
import useExpanded from 'hooks/useExpanded';
import { getQSConfig, parseQueryString } from 'util/qs';
import useWsTemplates from 'hooks/useWsTemplates';
import useToast, { AlertVariant } from 'hooks/useToast';
import { relatedResourceDeleteRequests } from 'util/getRelatedResourceDeleteDetails';
import AlertModal from '../AlertModal';
import DatalistToolbar from '../DataListToolbar';
import ErrorDetail from '../ErrorDetail';
import PaginatedTable, {
  HeaderRow,
  HeaderCell,
  ToolbarDeleteButton,
  getSearchableKeys,
} from '../PaginatedTable';
import AddDropDownButton from '../AddDropDownButton';
import TemplateListItem from './TemplateListItem';

function TemplateList({ defaultParams }) {
  // The type value in const qsConfig below does not have a space between job_template and
  // workflow_job_template so the params sent to the API match what the api expects.
  const qsConfig = getQSConfig(
    'template',
    {
      page: 1,
      page_size: 20,
      order_by: 'name',
      type: 'job_template,workflow_job_template',
      ...defaultParams,
    },
    ['id', 'page', 'page_size']
  );

  const location = useLocation();
  const { addToast, Toast, toastProps } = useToast();

  const {
    result: {
      results,
      count,
      jtActions,
      wfjtActions,
      relatedSearchableKeys,
      searchableKeys,
    },
    error: contentError,
    isLoading,
    request: fetchTemplates,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(qsConfig, location.search);
      const responses = await Promise.all([
        UnifiedJobTemplatesAPI.read(params),
        JobTemplatesAPI.readOptions(),
        WorkflowJobTemplatesAPI.readOptions(),
        UnifiedJobTemplatesAPI.readOptions(),
      ]);
      return {
        results: responses[0].data.results,
        count: responses[0].data.count,
        jtActions: responses[1].data.actions,
        wfjtActions: responses[2].data.actions,
        relatedSearchableKeys: (
          responses[3]?.data?.related_search_fields || []
        ).map((val) => val.slice(0, -8)),
        searchableKeys: getSearchableKeys(responses[3].data.actions?.GET),
      };
    }, [location]), // eslint-disable-line react-hooks/exhaustive-deps
    {
      results: [],
      count: 0,
      jtActions: {},
      wfjtActions: {},
      relatedSearchableKeys: [],
      searchableKeys: [],
    }
  );

  useEffect(() => {
    fetchTemplates();
  }, [fetchTemplates]);

  const templates = useWsTemplates(results);

  const { selected, isAllSelected, handleSelect, selectAll, clearSelected } =
    useSelected(templates);

  const { expanded, isAllExpanded, handleExpand, expandAll } =
    useExpanded(templates);

  const {
    isLoading: isDeleteLoading,
    deleteItems: deleteTemplates,
    deletionError,
    clearDeletionError,
  } = useDeleteItems(
    useCallback(
      () =>
        Promise.all(
          selected.map(({ type, id }) => {
            if (type === 'job_template') {
              return JobTemplatesAPI.destroy(id);
            }
            if (type === 'workflow_job_template') {
              return WorkflowJobTemplatesAPI.destroy(id);
            }
            return false;
          })
        ),
      [selected]
    ),
    {
      qsConfig,
      allItemsSelected: isAllSelected,
      fetchItems: fetchTemplates,
    }
  );

  const handleCopy = useCallback(
    (newTemplateId) => {
      addToast({
        id: newTemplateId,
        title: t`Template copied successfully`,
        variant: AlertVariant.success,
        hasTimeout: true,
      });
    },
    [addToast]
  );

  const handleTemplateDelete = async () => {
    await deleteTemplates();
    clearSelected();
  };

  const canAddJT =
    jtActions && Object.prototype.hasOwnProperty.call(jtActions, 'POST');
  const canAddWFJT =
    wfjtActions && Object.prototype.hasOwnProperty.call(wfjtActions, 'POST');

  const addTemplate = t`Add job template`;
  const addWFTemplate = t`Add workflow template`;
  const addDropDownButton = [];
  if (canAddJT) {
    addDropDownButton.push(
      <DropdownItem
        ouiaId="add-job-template-item"
        key={addTemplate}
        component={Link}
        to="/templates/job_template/add/"
        aria-label={addTemplate}
      >
        {addTemplate}
      </DropdownItem>
    );
  }
  if (canAddWFJT) {
    addDropDownButton.push(
      <DropdownItem
        ouiaId="add-workflow-job-template-item"
        component={Link}
        to="/templates/workflow_job_template/add/"
        key={addWFTemplate}
        aria-label={addWFTemplate}
      >
        {addWFTemplate}
      </DropdownItem>
    );
  }
  const addButton = (
    <AddDropDownButton
      ouiaId="add-template-button"
      key="add"
      dropdownItems={addDropDownButton}
    />
  );

  const deleteDetailsRequests = relatedResourceDeleteRequests.template(
    selected[0]
  );

  return (
    <>
      <Card>
        <PaginatedTable
          contentError={contentError}
          hasContentLoading={isLoading || isDeleteLoading}
          items={templates}
          itemCount={count}
          pluralizedItemName={t`Templates`}
          qsConfig={qsConfig}
          clearSelected={clearSelected}
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
              name: t`Type`,
              key: 'or__type',
              options: [
                [`job_template`, t`Job Template`],
                [`workflow_job_template`, t`Workflow Template`],
              ],
            },
            {
              name: t`Playbook name`,
              key: 'job_template__playbook__icontains',
            },
            {
              name: t`Created By (Username)`,
              key: 'created_by__username__icontains',
            },
            {
              name: t`Modified By (Username)`,
              key: 'modified_by__username__icontains',
            },
            {
              name: t`Label`,
              key: 'labels__name__icontains',
            },
          ]}
          toolbarSearchableKeys={searchableKeys}
          toolbarRelatedSearchableKeys={relatedSearchableKeys}
          headerRow={
            <HeaderRow qsConfig={qsConfig} isExpandable>
              <HeaderCell sortKey="name">{t`Name`}</HeaderCell>
              <HeaderCell sortKey="type">{t`Type`}</HeaderCell>
              <HeaderCell sortKey="last_job_run">{t`Last Ran`}</HeaderCell>
              <HeaderCell>{t`Actions`}</HeaderCell>
            </HeaderRow>
          }
          renderToolbar={(props) => (
            <DatalistToolbar
              {...props}
              isAllSelected={isAllSelected}
              onSelectAll={selectAll}
              isAllExpanded={isAllExpanded}
              onExpandAll={expandAll}
              qsConfig={qsConfig}
              additionalControls={[
                ...(canAddJT || canAddWFJT ? [addButton] : []),
                <ToolbarDeleteButton
                  key="delete"
                  onDelete={handleTemplateDelete}
                  itemsToDelete={selected}
                  pluralizedItemName={t`Templates`}
                  deleteDetailsRequests={deleteDetailsRequests}
                  deleteMessage={
                    <Plural
                      value={selected.length}
                      one="This template is currently being used by some workflow nodes. Are you sure you want to delete it?"
                      other="Deleting these templates could impact some workflow nodes that rely on them. Are you sure you want to delete anyway?"
                    />
                  }
                />,
              ]}
            />
          )}
          renderRow={(template, index) => (
            <TemplateListItem
              key={template.id}
              value={template.name}
              template={template}
              detailUrl={`/templates/${template.type}/${template.id}`}
              onSelect={() => handleSelect(template)}
              isExpanded={expanded.some((row) => row.id === template.id)}
              onExpand={() => handleExpand(template)}
              onCopy={handleCopy}
              isSelected={selected.some((row) => row.id === template.id)}
              fetchTemplates={fetchTemplates}
              rowIndex={index}
            />
          )}
          emptyStateControls={(canAddJT || canAddWFJT) && addButton}
        />
      </Card>
      <Toast {...toastProps} />
      <AlertModal
        aria-label={t`Deletion Error`}
        isOpen={deletionError}
        variant="error"
        title={t`Error!`}
        onClose={clearDeletionError}
      >
        {t`Failed to delete one or more templates.`}
        <ErrorDetail error={deletionError} />
      </AlertModal>
    </>
  );
}

export default TemplateList;
