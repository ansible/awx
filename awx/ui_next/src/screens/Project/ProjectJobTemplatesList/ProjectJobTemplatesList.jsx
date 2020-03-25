import React, { useEffect, useState } from 'react';
import { useParams, useLocation } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Card } from '@patternfly/react-core';

import {
  JobTemplatesAPI,
  UnifiedJobTemplatesAPI,
  WorkflowJobTemplatesAPI,
} from '@api';
import AlertModal from '@components/AlertModal';
import DatalistToolbar from '@components/DataListToolbar';
import ErrorDetail from '@components/ErrorDetail';
import PaginatedDataList, {
  ToolbarAddButton,
  ToolbarDeleteButton,
} from '@components/PaginatedDataList';
import { getQSConfig, parseQueryString } from '@util/qs';
import ProjectTemplatesListItem from './ProjectJobTemplatesListItem';

// The type value in const QS_CONFIG below does not have a space between job_template and
// workflow_job_template so the params sent to the API match what the api expects.
const QS_CONFIG = getQSConfig('template', {
  page: 1,
  page_size: 20,
  order_by: 'name',
  type: 'job_template,workflow_job_template',
});

function ProjectJobTemplatesList({ i18n }) {
  const { id: projectId } = useParams();
  const { pathname, search } = useLocation();

  const [deletionError, setDeletionError] = useState(null);
  const [contentError, setContentError] = useState(null);
  const [hasContentLoading, setHasContentLoading] = useState(true);
  const [jtActions, setJTActions] = useState(null);
  const [wfjtActions, setWFJTActions] = useState(null);
  const [count, setCount] = useState(0);
  const [templates, setTemplates] = useState([]);
  const [selected, setSelected] = useState([]);

  useEffect(
    () => {
      const loadTemplates = async () => {
        const params = {
          ...parseQueryString(QS_CONFIG, search),
        };

        let jtOptionsPromise;
        if (jtActions) {
          jtOptionsPromise = Promise.resolve({
            data: { actions: jtActions },
          });
        } else {
          jtOptionsPromise = JobTemplatesAPI.readOptions();
        }

        let wfjtOptionsPromise;
        if (wfjtActions) {
          wfjtOptionsPromise = Promise.resolve({
            data: { actions: wfjtActions },
          });
        } else {
          wfjtOptionsPromise = WorkflowJobTemplatesAPI.readOptions();
        }
        if (pathname.startsWith('/projects') && projectId) {
          params.jobtemplate__project = projectId;
        }

        const promises = Promise.all([
          UnifiedJobTemplatesAPI.read(params),
          jtOptionsPromise,
          wfjtOptionsPromise,
        ]);
        setDeletionError(null);

        try {
          const [
            {
              data: { count: itemCount, results },
            },
            {
              data: { actions: jobTemplateActions },
            },
            {
              data: { actions: workFlowJobTemplateActions },
            },
          ] = await promises;
          setJTActions(jobTemplateActions);
          setWFJTActions(workFlowJobTemplateActions);
          setCount(itemCount);
          setTemplates(results);
          setHasContentLoading(false);
        } catch (err) {
          setContentError(err);
        }
      };
      loadTemplates();
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [pathname, search, count, projectId]
  );

  const handleSelectAll = isSelected => {
    const selectedItems = isSelected ? [...templates] : [];
    setSelected(selectedItems);
  };

  const handleSelect = template => {
    if (selected.some(s => s.id === template.id)) {
      setSelected(selected.filter(s => s.id !== template.id));
    } else {
      setSelected(selected.concat(template));
    }
  };

  const handleTemplateDelete = async () => {
    setHasContentLoading(true);
    try {
      await Promise.all(
        selected.map(({ type, id }) => {
          let deletePromise;
          if (type === 'job_template') {
            deletePromise = JobTemplatesAPI.destroy(id);
          } else if (type === 'workflow_job_template') {
            deletePromise = WorkflowJobTemplatesAPI.destroy(id);
          }
          return deletePromise;
        })
      );
      setCount(count - selected.length);
    } catch (err) {
      setDeletionError(err);
    }
  };

  const canAddJT =
    jtActions && Object.prototype.hasOwnProperty.call(jtActions, 'POST');

  const addButton = (
    <ToolbarAddButton key="add" linkTo="/templates/job_template/add/" />
  );

  const isAllSelected =
    selected.length === templates.length && selected.length > 0;

  return (
    <>
      <Card>
        <PaginatedDataList
          contentError={contentError}
          hasContentLoading={hasContentLoading}
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
                ...(canAddJT ? [addButton] : []),
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
        onClose={() => setDeletionError(null)}
      >
        {i18n._(t`Failed to delete one or more templates.`)}
        <ErrorDetail error={deletionError} />
      </AlertModal>
    </>
  );
}

export default withI18n()(ProjectJobTemplatesList);
