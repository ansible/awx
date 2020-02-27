import React, { useState, useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import { Card } from '@patternfly/react-core';
import AlertModal from '@components/AlertModal';
import DatalistToolbar from '@components/DataListToolbar';
import ErrorDetail from '@components/ErrorDetail';
import PaginatedDataList, {
  ToolbarDeleteButton,
} from '@components/PaginatedDataList';
import useRequest, { useDeleteItems } from '@util/useRequest';
import { getQSConfig, parseQueryString } from '@util/qs';
import JobListItem from './JobListItem';
import {
  AdHocCommandsAPI,
  InventoryUpdatesAPI,
  JobsAPI,
  ProjectUpdatesAPI,
  SystemJobsAPI,
  UnifiedJobsAPI,
  WorkflowJobsAPI,
} from '@api';

const QS_CONFIG = getQSConfig(
  'job',
  {
    page: 1,
    page_size: 20,
    order_by: '-finished',
  },
  ['page', 'page_size']
);

function JobList({ i18n, defaultParams, showTypeColumn = false }) {
  const [selected, setSelected] = useState([]);
  const location = useLocation();

  const {
    result: { jobs, itemCount },
    error: contentError,
    isLoading,
    request: fetchJobs,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);

      const {
        data: { count, results },
      } = await UnifiedJobsAPI.read({ ...params, ...defaultParams });

      return {
        itemCount: count,
        jobs: results,
      };
    }, [location]), // eslint-disable-line react-hooks/exhaustive-deps
    {
      jobs: [],
      itemCount: 0,
    }
  );

  useEffect(() => {
    fetchJobs();
  }, [fetchJobs]);

  const isAllSelected = selected.length === jobs.length && selected.length > 0;
  const {
    isLoading: isDeleteLoading,
    deleteItems: deleteJobs,
    deletionError,
    clearDeletionError,
  } = useDeleteItems(
    useCallback(async () => {
      return Promise.all(
        selected.map(({ type, id }) => {
          switch (type) {
            case 'job':
              return JobsAPI.destroy(id);
            case 'ad_hoc_command':
              return AdHocCommandsAPI.destroy(id);
            case 'system_job':
              return SystemJobsAPI.destroy(id);
            case 'project_update':
              return ProjectUpdatesAPI.destroy(id);
            case 'inventory_update':
              return InventoryUpdatesAPI.destroy(id);
            case 'workflow_job':
              return WorkflowJobsAPI.destroy(id);
            default:
              return null;
          }
        })
      );
    }, [selected]),
    {
      qsConfig: QS_CONFIG,
      allItemsSelected: isAllSelected,
      fetchItems: fetchJobs,
    }
  );

  const handleJobDelete = async () => {
    await deleteJobs();
    setSelected([]);
  };

  const handleSelectAll = isSelected => {
    setSelected(isSelected ? [...jobs] : []);
  };

  const handleSelect = item => {
    if (selected.some(s => s.id === item.id)) {
      setSelected(selected.filter(s => s.id !== item.id));
    } else {
      setSelected(selected.concat(item));
    }
  };

  return (
    <>
      <Card>
        <PaginatedDataList
          contentError={contentError}
          hasContentLoading={isLoading || isDeleteLoading}
          items={jobs}
          itemCount={itemCount}
          pluralizedItemName="Jobs"
          qsConfig={QS_CONFIG}
          onRowClick={handleSelect}
          toolbarSearchColumns={[
            {
              name: i18n._(t`Name`),
              key: 'name',
              isDefault: true,
            },
            {
              name: i18n._(t`ID`),
              key: 'id',
            },
            {
              name: i18n._(t`Label Name`),
              key: 'labels__name',
            },
            {
              name: i18n._(t`Job Type`),
              key: `type`,
              options: [
                [`project_update`, i18n._(t`SCM Update`)],
                [`inventory_update`, i18n._(t`Inventory Sync`)],
                [`job`, i18n._(t`Playbook Run`)],
                [`ad_hoc_command`, i18n._(t`Command`)],
                [`system_job`, i18n._(t`Management Job`)],
                [`workflow_job`, i18n._(t`Workflow Job`)],
              ],
            },
            {
              name: i18n._(t`Launched By (Username)`),
              key: 'created_by__username',
            },
            {
              name: i18n._(t`Status`),
              key: 'status',
              options: [
                [`new`, i18n._(t`New`)],
                [`pending`, i18n._(t`Pending`)],
                [`waiting`, i18n._(t`Waiting`)],
                [`running`, i18n._(t`Running`)],
                [`successful`, i18n._(t`Successful`)],
                [`failed`, i18n._(t`Failed`)],
                [`error`, i18n._(t`Error`)],
                [`canceled`, i18n._(t`Canceled`)],
              ],
            },
            {
              name: i18n._(t`Limit`),
              key: 'job__limit',
            },
          ]}
          toolbarSortColumns={[
            {
              name: i18n._(t`Finish Time`),
              key: 'finished',
            },
            {
              name: i18n._(t`ID`),
              key: 'id',
            },
            {
              name: i18n._(t`Launched By`),
              key: 'created_by__id',
            },
            {
              name: i18n._(t`Name`),
              key: 'name',
            },
            {
              name: i18n._(t`Project`),
              key: 'unified_job_template__project__id',
            },
            {
              name: i18n._(t`Start Time`),
              key: 'started',
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
                <ToolbarDeleteButton
                  key="delete"
                  onDelete={handleJobDelete}
                  itemsToDelete={selected}
                  pluralizedItemName="Jobs"
                />,
              ]}
            />
          )}
          renderItem={job => (
            <JobListItem
              key={job.id}
              job={job}
              showTypeColumn={showTypeColumn}
              onSelect={() => handleSelect(job)}
              isSelected={selected.some(row => row.id === job.id)}
            />
          )}
        />
      </Card>
      <AlertModal
        isOpen={deletionError}
        variant="error"
        title={i18n._(t`Error!`)}
        onClose={clearDeletionError}
      >
        {i18n._(t`Failed to delete one or more jobs.`)}
        <ErrorDetail error={deletionError} />
      </AlertModal>
    </>
  );
}

export default withI18n()(JobList);
