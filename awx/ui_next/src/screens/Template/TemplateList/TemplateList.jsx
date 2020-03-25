import React, { useEffect, useState, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Card, PageSection } from '@patternfly/react-core';

import {
  JobTemplatesAPI,
  UnifiedJobTemplatesAPI,
  WorkflowJobTemplatesAPI,
} from '@api';
import AlertModal from '@components/AlertModal';
import DatalistToolbar from '@components/DataListToolbar';
import ErrorDetail from '@components/ErrorDetail';
import PaginatedDataList, {
  ToolbarDeleteButton,
} from '@components/PaginatedDataList';
import useRequest, { useDeleteItems } from '@util/useRequest';
import { getQSConfig, parseQueryString } from '@util/qs';

import AddDropDownButton from '@components/AddDropDownButton';
import TemplateListItem from './TemplateListItem';

// The type value in const QS_CONFIG below does not have a space between job_template and
// workflow_job_template so the params sent to the API match what the api expects.
const QS_CONFIG = getQSConfig('template', {
  page: 1,
  page_size: 20,
  order_by: 'name',
  type: 'job_template,workflow_job_template',
});

function TemplateList({ i18n }) {
  const location = useLocation();

  const [selected, setSelected] = useState([]);

  const {
    result: { templates, count, jtActions, wfjtActions },
    error: contentError,
    isLoading,
    request: fetchTemplates,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);
      const results = await Promise.all([
        UnifiedJobTemplatesAPI.read(params),
        JobTemplatesAPI.readOptions(),
        WorkflowJobTemplatesAPI.readOptions(),
      ]);
      return {
        templates: results[0].data.results,
        count: results[0].data.count,
        jtActions: results[1].data.actions,
        wfjtActions: results[2].data.actions,
      };
    }, [location]),
    {
      templates: [],
      count: 0,
      jtActions: {},
      wfjtActions: {},
    }
  );

  useEffect(() => {
    fetchTemplates();
  }, [fetchTemplates]);

  const isAllSelected =
    selected.length === templates.length && selected.length > 0;
  const {
    isLoading: isDeleteLoading,
    deleteItems: deleteTemplates,
    deletionError,
    clearDeletionError,
  } = useDeleteItems(
    useCallback(async () => {
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
      qsConfig: QS_CONFIG,
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
  const addButtonOptions = [];

  if (canAddJT) {
    addButtonOptions.push({
      label: i18n._(t`Template`),
      url: `/templates/job_template/add/`,
    });
  }

  if (canAddWFJT) {
    addButtonOptions.push({
      label: i18n._(t`Workflow Template`),
      url: `/templates/workflow_job_template/add/`,
    });
  }

  const addButton = (
    <AddDropDownButton key="add" dropdownItems={addButtonOptions} />
  );

  return (
    <PageSection>
      <Card>
        <PaginatedDataList
          contentError={contentError}
          hasContentLoading={isLoading || isDeleteLoading}
          items={templates}
          itemCount={count}
          pluralizedItemName={i18n._(t`Templates`)}
          qsConfig={QS_CONFIG}
          onRowClick={handleSelect}
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
                [`job_template`, i18n._(t`Job Template`)],
                [`workflow_job_template`, i18n._(t`Workflow Template`)],
              ],
            },
            {
              name: i18n._(t`Playbook name`),
              key: 'job_template__playbook',
            },
            {
              name: i18n._(t`Created By (Username)`),
              key: 'created_by__username',
            },
            {
              name: i18n._(t`Modified By (Username)`),
              key: 'modified_by__username',
            },
          ]}
          toolbarSortColumns={[
            {
              name: i18n._(t`Inventory`),
              key: 'job_template__inventory__id',
            },
            {
              name: i18n._(t`Last Job Run`),
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
              onSelectAll={handleSelectAll}
              qsConfig={QS_CONFIG}
              additionalControls={[
                ...(canAddJT || canAddWFJT ? [addButton] : []),
                <ToolbarDeleteButton
                  key="delete"
                  onDelete={handleTemplateDelete}
                  itemsToDelete={selected}
                  pluralizedItemName="Templates"
                />,
              ]}
            />
          )}
          renderItem={template => (
            <TemplateListItem
              key={template.id}
              value={template.name}
              template={template}
              detailUrl={`/templates/${template.type}/${template.id}`}
              onSelect={() => handleSelect(template)}
              isSelected={selected.some(row => row.id === template.id)}
            />
          )}
          emptyStateControls={(canAddJT || canAddWFJT) && addButton}
        />
      </Card>
      <AlertModal
        isOpen={deletionError}
        variant="error"
        title={i18n._(t`Error!`)}
        onClose={clearDeletionError}
      >
        {i18n._(t`Failed to delete one or more templates.`)}
        <ErrorDetail error={deletionError} />
      </AlertModal>
    </PageSection>
  );
}

export default withI18n()(TemplateList);
