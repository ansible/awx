import React, { useState, useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';

import { t, plural } from '@lingui/macro';

import { Card } from '@patternfly/react-core';
import AlertModal from '../AlertModal';
import DatalistToolbar from '../DataListToolbar';
import ErrorDetail from '../ErrorDetail';
import { ToolbarDeleteButton } from '../PaginatedDataList';
import PaginatedTable, { HeaderRow, HeaderCell } from '../PaginatedTable';
import useRequest, {
  useDeleteItems,
  useDismissableError,
} from '../../util/useRequest';
import { isJobRunning, getJobModel } from '../../util/jobs';
import { getQSConfig, parseQueryString } from '../../util/qs';
import JobListItem from './JobListItem';
import JobListCancelButton from './JobListCancelButton';
import useWsJobs from './useWsJobs';
import { UnifiedJobsAPI } from '../../api';

function JobList({ defaultParams, showTypeColumn = false }) {
  const qsConfig = getQSConfig(
    'job',
    {
      page: 1,
      page_size: 20,
      order_by: '-finished',
      not__launch_type: 'sync',
      ...defaultParams,
    },
    ['id', 'page', 'page_size']
  );

  const [selected, setSelected] = useState([]);
  const location = useLocation();
  const {
    result: { results, count, relatedSearchableKeys, searchableKeys },
    error: contentError,
    isLoading,
    request: fetchJobs,
  } = useRequest(
    useCallback(
      async () => {
        const params = parseQueryString(qsConfig, location.search);
        const [response, actionsResponse] = await Promise.all([
          UnifiedJobsAPI.read({ ...params }),
          UnifiedJobsAPI.readOptions(),
        ]);
        return {
          results: response.data.results,
          count: response.data.count,
          relatedSearchableKeys: (
            actionsResponse?.data?.related_search_fields || []
          ).map(val => val.slice(0, -8)),
          searchableKeys: Object.keys(
            actionsResponse.data.actions?.GET || {}
          ).filter(key => actionsResponse.data.actions?.GET[key].filterable),
        };
      },
      [location] // eslint-disable-line react-hooks/exhaustive-deps
    ),
    {
      results: [],
      count: 0,
      relatedSearchableKeys: [],
      searchableKeys: [],
    }
  );
  useEffect(() => {
    fetchJobs();
  }, [fetchJobs]);

  // TODO: update QS_CONFIG to be safe for deps array
  const fetchJobsById = useCallback(
    async ids => {
      const params = parseQueryString(qsConfig, location.search);
      params.id__in = ids.join(',');
      const { data } = await UnifiedJobsAPI.read(params);
      return data.results;
    },
    [location.search] // eslint-disable-line react-hooks/exhaustive-deps
  );

  const jobs = useWsJobs(results, fetchJobsById, qsConfig);

  const isAllSelected = selected.length === jobs.length && selected.length > 0;

  const {
    error: cancelJobsError,
    isLoading: isCancelLoading,
    request: cancelJobs,
  } = useRequest(
    useCallback(async () => {
      return Promise.all(
        selected.map(job => {
          if (isJobRunning(job.status)) {
            return getJobModel(job.type).cancel(job.id);
          }
          return Promise.resolve();
        })
      );
    }, [selected]),
    {}
  );

  const {
    error: cancelError,
    dismissError: dismissCancelError,
  } = useDismissableError(cancelJobsError);

  const {
    isLoading: isDeleteLoading,
    deleteItems: deleteJobs,
    deletionError,
    clearDeletionError,
  } = useDeleteItems(
    useCallback(() => {
      return Promise.all(
        selected.map(({ type, id }) => {
          return getJobModel(type).destroy(id);
        })
      );
    }, [selected]),
    {
      qsConfig,
      allItemsSelected: isAllSelected,
      fetchItems: fetchJobs,
    }
  );

  const handleJobCancel = async () => {
    await cancelJobs();
    setSelected([]);
  };

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

  const cannotDeleteItems = selected.filter(job => isJobRunning(job.status));

  return (
    <>
      <Card>
        <PaginatedTable
          contentError={contentError}
          hasContentLoading={isLoading || isDeleteLoading || isCancelLoading}
          items={jobs}
          itemCount={count}
          pluralizedItemName={t`Jobs`}
          qsConfig={qsConfig}
          toolbarSearchColumns={[
            {
              name: t`Name`,
              key: 'name__icontains',
              isDefault: true,
            },
            {
              name: t`ID`,
              key: 'id',
            },
            {
              name: t`Label Name`,
              key: 'labels__name__icontains',
            },
            {
              name: t`Job Type`,
              key: `or__type`,
              options: [
                [`project_update`, t`Source Control Update`],
                [`inventory_update`, t`Inventory Sync`],
                [`job`, t`Playbook Run`],
                [`ad_hoc_command`, t`Command`],
                [`system_job`, t`Management Job`],
                [`workflow_job`, t`Workflow Job`],
              ],
            },
            {
              name: t`Launched By (Username)`,
              key: 'created_by__username__icontains',
            },
            {
              name: t`Status`,
              key: 'status',
              options: [
                [`new`, t`New`],
                [`pending`, t`Pending`],
                [`waiting`, t`Waiting`],
                [`running`, t`Running`],
                [`successful`, t`Successful`],
                [`failed`, t`Failed`],
                [`error`, t`Error`],
                [`canceled`, t`Canceled`],
              ],
            },
            {
              name: t`Limit`,
              key: 'job__limit',
            },
          ]}
          headerRow={
            <HeaderRow qsConfig={qsConfig} isExpandable>
              <HeaderCell sortKey="name">{t`Name`}</HeaderCell>
              <HeaderCell sortKey="status">{t`Status`}</HeaderCell>
              {showTypeColumn && <HeaderCell>{t`Type`}</HeaderCell>}
              <HeaderCell sortKey="started">{t`Start Time`}</HeaderCell>
              <HeaderCell sortKey="finished">{t`Finish Time`}</HeaderCell>
              <HeaderCell>{t`Actions`}</HeaderCell>
            </HeaderRow>
          }
          toolbarSearchableKeys={searchableKeys}
          toolbarRelatedSearchableKeys={relatedSearchableKeys}
          renderToolbar={props => (
            <DatalistToolbar
              {...props}
              showSelectAll
              isAllSelected={isAllSelected}
              onSelectAll={handleSelectAll}
              qsConfig={qsConfig}
              additionalControls={[
                <ToolbarDeleteButton
                  key="delete"
                  onDelete={handleJobDelete}
                  itemsToDelete={selected}
                  pluralizedItemName={t`Jobs`}
                  cannotDelete={item =>
                    isJobRunning(item.status) ||
                    !item.summary_fields.user_capabilities.delete
                  }
                  errorMessage={plural(cannotDeleteItems.length, {
                    one:
                      'The selected job cannot be deleted due to insufficient permission or a running job status',
                    other:
                      'The selected jobs cannot be deleted due to insufficient permissions or a running job status',
                  })}
                />,
                <JobListCancelButton
                  key="cancel"
                  onCancel={handleJobCancel}
                  jobsToCancel={selected}
                />,
              ]}
            />
          )}
          renderRow={(job, index) => (
            <JobListItem
              key={job.id}
              job={job}
              showTypeColumn={showTypeColumn}
              onSelect={() => handleSelect(job)}
              isSelected={selected.some(row => row.id === job.id)}
              rowIndex={index}
            />
          )}
        />
      </Card>
      {deletionError && (
        <AlertModal
          isOpen
          variant="error"
          title={t`Error!`}
          onClose={clearDeletionError}
        >
          {t`Failed to delete one or more jobs.`}
          <ErrorDetail error={deletionError} />
        </AlertModal>
      )}
      {cancelError && (
        <AlertModal
          isOpen
          variant="error"
          title={t`Error!`}
          onClose={dismissCancelError}
        >
          {t`Failed to cancel one or more jobs.`}
          <ErrorDetail error={cancelError} />
        </AlertModal>
      )}
    </>
  );
}

export default JobList;
