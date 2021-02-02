import React, { Fragment, useEffect, useState, useCallback } from 'react';
import { useLocation, Link } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Card, DropdownItem } from '@patternfly/react-core';
import {
  JobTemplatesAPI,
  UnifiedJobTemplatesAPI,
  WorkflowJobTemplatesAPI,
} from '../../api';
import AlertModal from '../AlertModal';
import DatalistToolbar from '../DataListToolbar';
import ErrorDetail from '../ErrorDetail';
import { ToolbarDeleteButton } from '../PaginatedDataList';
import PaginatedTable, { HeaderRow, HeaderCell } from '../PaginatedTable';
import useRequest, { useDeleteItems } from '../../util/useRequest';
import { getQSConfig, parseQueryString } from '../../util/qs';
import useWsTemplates from '../../util/useWsTemplates';
import AddDropDownButton from '../AddDropDownButton';
import TemplateListItem from './TemplateListItem';

function TemplateList({ defaultParams, i18n }) {
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
  const [selected, setSelected] = useState([]);

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
        ).map(val => val.slice(0, -8)),
        searchableKeys: Object.keys(
          responses[3].data.actions?.GET || {}
        ).filter(key => responses[3].data.actions?.GET[key].filterable),
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

  const isAllSelected =
    selected.length === templates.length && selected.length > 0;
  const {
    isLoading: isDeleteLoading,
    deleteItems: deleteTemplates,
    deletionError,
    clearDeletionError,
  } = useDeleteItems(
    useCallback(() => {
      return Promise.all(
        selected.map(({ type, id }) => {
          if (type === 'job_template') {
            return JobTemplatesAPI.destroy(id);
          }
          if (type === 'workflow_job_template') {
            return WorkflowJobTemplatesAPI.destroy(id);
          }
          return false;
        })
      );
    }, [selected]),
    {
      qsConfig,
      allItemsSelected: isAllSelected,
      fetchItems: fetchTemplates,
    }
  );

  const handleTemplateDelete = async () => {
    await deleteTemplates();
    setSelected([]);
  };

  const handleSelectAll = isSelected => {
    setSelected(isSelected ? [...templates] : []);
  };

  const handleSelect = template => {
    if (selected.some(s => s.id === template.id)) {
      setSelected(selected.filter(s => s.id !== template.id));
    } else {
      setSelected(selected.concat(template));
    }
  };

  const canAddJT =
    jtActions && Object.prototype.hasOwnProperty.call(jtActions, 'POST');
  const canAddWFJT =
    wfjtActions && Object.prototype.hasOwnProperty.call(wfjtActions, 'POST');

  const addTemplate = i18n._(t`Add job template`);
  const addWFTemplate = i18n._(t`Add workflow template`);
  const addDropDownButton = [];
  if (canAddJT) {
    addDropDownButton.push(
      <DropdownItem
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
    <AddDropDownButton key="add" dropdownItems={addDropDownButton} />
  );

  return (
    <Fragment>
      <Card>
        <PaginatedTable
          contentError={contentError}
          hasContentLoading={isLoading || isDeleteLoading}
          items={templates}
          itemCount={count}
          pluralizedItemName={i18n._(t`Templates`)}
          qsConfig={qsConfig}
          onRowClick={handleSelect}
          toolbarSearchColumns={[
            {
              name: i18n._(t`Name`),
              key: 'name__icontains',
              isDefault: true,
            },
            {
              name: i18n._(t`Description`),
              key: 'description__icontains',
            },
            {
              name: i18n._(t`Type`),
              key: 'or__type',
              options: [
                [`job_template`, i18n._(t`Job Template`)],
                [`workflow_job_template`, i18n._(t`Workflow Template`)],
              ],
            },
            {
              name: i18n._(t`Playbook name`),
              key: 'job_template__playbook__icontains',
            },
            {
              name: i18n._(t`Created By (Username)`),
              key: 'created_by__username__icontains',
            },
            {
              name: i18n._(t`Modified By (Username)`),
              key: 'modified_by__username__icontains',
            },
          ]}
          toolbarSearchableKeys={searchableKeys}
          toolbarRelatedSearchableKeys={relatedSearchableKeys}
          headerRow={
            <HeaderRow qsConfig={qsConfig} isExpandable>
              <HeaderCell sortKey="name">{i18n._(t`Name`)}</HeaderCell>
              <HeaderCell sortKey="type">{i18n._(t`Type`)}</HeaderCell>
              <HeaderCell sortKey="last_job_run">
                {i18n._(t`Last Ran`)}
              </HeaderCell>
              <HeaderCell>{i18n._(t`Actions`)}</HeaderCell>
            </HeaderRow>
          }
          renderToolbar={props => (
            <DatalistToolbar
              {...props}
              showSelectAll
              isAllSelected={isAllSelected}
              onSelectAll={handleSelectAll}
              qsConfig={qsConfig}
              additionalControls={[
                ...(canAddJT || canAddWFJT ? [addButton] : []),
                <ToolbarDeleteButton
                  key="delete"
                  onDelete={handleTemplateDelete}
                  itemsToDelete={selected}
                  pluralizedItemName={i18n._(t`Templates`)}
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
              isSelected={selected.some(row => row.id === template.id)}
              fetchTemplates={fetchTemplates}
              rowIndex={index}
            />
          )}
          emptyStateControls={(canAddJT || canAddWFJT) && addButton}
        />
      </Card>
      <AlertModal
        aria-label={i18n._(t`Deletion Error`)}
        isOpen={deletionError}
        variant="error"
        title={i18n._(t`Error!`)}
        onClose={clearDeletionError}
      >
        {i18n._(t`Failed to delete one or more templates.`)}
        <ErrorDetail error={deletionError} />
      </AlertModal>
    </Fragment>
  );
}

export default withI18n()(TemplateList);
