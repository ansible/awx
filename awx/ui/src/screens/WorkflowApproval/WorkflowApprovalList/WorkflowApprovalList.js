import React, { useCallback, useEffect, useState } from 'react';
import { useLocation, useRouteMatch } from 'react-router-dom';
import { t, Plural } from '@lingui/macro';
import { Card, PageSection } from '@patternfly/react-core';
import { WorkflowApprovalsAPI, WorkflowJobsAPI } from 'api';
import PaginatedTable, {
  HeaderRow,
  HeaderCell,
  ToolbarDeleteButton,
  getSearchableKeys,
} from 'components/PaginatedTable';
import AlertModal from 'components/AlertModal';
import ErrorDetail from 'components/ErrorDetail';
import DataListToolbar from 'components/DataListToolbar';
import useRequest, {
  useDeleteItems,
  useDismissableError,
} from 'hooks/useRequest';
import useSelected from 'hooks/useSelected';
import { getQSConfig, parseQueryString } from 'util/qs';
import WorkflowApprovalListItem from './WorkflowApprovalListItem';
import useWsWorkflowApprovals from './useWsWorkflowApprovals';
import WorkflowApprovalControls from '../shared/WorkflowApprovalControls';

const QS_CONFIG = getQSConfig('workflow_approvals', {
  page: 1,
  page_size: 20,
  order_by: '-started',
});

function WorkflowApprovalsList() {
  const location = useLocation();
  const match = useRouteMatch();
  const [isKebabOpen, setIsKebabModalOpen] = useState(false);

  const {
    result: { results, count, relatedSearchableKeys, searchableKeys },
    error: contentError,
    isLoading: isWorkflowApprovalsLoading,
    request: fetchWorkflowApprovals,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);
      const [response, actionsResponse] = await Promise.all([
        WorkflowApprovalsAPI.read(params),
        WorkflowApprovalsAPI.readOptions(),
      ]);
      const dataWithModifiedName = response.data.results.map((i) => {
        i.name = `${i.summary_fields.source_workflow_job.id} - ${i.name}`;
        return i;
      });
      return {
        results: dataWithModifiedName,
        count: response.data.count,
        relatedSearchableKeys: (
          actionsResponse?.data?.related_search_fields || []
        ).map((val) => val.slice(0, -8)),
        searchableKeys: getSearchableKeys(actionsResponse.data.actions?.GET),
      };
    }, [location]),
    {
      results: [],
      count: 0,
      relatedSearchableKeys: [],
      searchableKeys: [],
    }
  );

  useEffect(() => {
    fetchWorkflowApprovals();
  }, [fetchWorkflowApprovals]);

  const fetchWorkflowApprovalsById = useCallback(
    async (ids) => {
      const params = { ...parseQueryString(QS_CONFIG, location.search) };
      params.id__in = ids.join(',');
      const { data } = await WorkflowApprovalsAPI.read(params);
      return data.results;
    },
    [location.search] // eslint-disable-line react-hooks/exhaustive-deps
  );

  const workflowApprovals = useWsWorkflowApprovals(
    results,
    fetchWorkflowApprovals,
    fetchWorkflowApprovalsById,
    QS_CONFIG
  );

  const { selected, isAllSelected, handleSelect, clearSelected, selectAll } =
    useSelected(workflowApprovals);

  const {
    isLoading: isDeleteLoading,
    deleteItems: deleteWorkflowApprovals,
    deletionError,
    clearDeletionError,
  } = useDeleteItems(
    useCallback(
      async () =>
        Promise.all(selected.map(({ id }) => WorkflowApprovalsAPI.destroy(id))),
      [selected]
    ),
    {
      qsConfig: QS_CONFIG,
      allItemsSelected: isAllSelected,
      fetchItems: fetchWorkflowApprovals,
    }
  );

  const handleDelete = async () => {
    await deleteWorkflowApprovals();
    clearSelected();
  };

  const {
    error: approveApprovalError,
    isLoading: isApproveLoading,
    request: approveWorkflowApprovals,
  } = useRequest(
    useCallback(
      async () =>
        Promise.all(selected.map(({ id }) => WorkflowApprovalsAPI.approve(id))),
      [selected]
    ),
    {}
  );

  const handleApprove = async () => {
    await approveWorkflowApprovals();
    clearSelected();
  };

  const {
    error: denyApprovalError,
    isLoading: isDenyLoading,
    request: denyWorkflowApprovals,
  } = useRequest(
    useCallback(
      async () =>
        Promise.all(selected.map(({ id }) => WorkflowApprovalsAPI.deny(id))),
      [selected]
    ),
    {}
  );

  const handleDeny = async () => {
    setIsKebabModalOpen(false);
    await denyWorkflowApprovals();
    clearSelected();
  };

  const {
    error: cancelApprovalError,
    isLoading: isCancelLoading,
    request: cancelWorkflowApprovals,
  } = useRequest(
    useCallback(
      async () =>
        Promise.all(
          selected.map(({ summary_fields }) =>
            WorkflowJobsAPI.cancel(summary_fields.source_workflow_job.id)
          )
        ),
      [selected]
    ),
    {}
  );

  const handleCancel = async () => {
    setIsKebabModalOpen(false);
    await cancelWorkflowApprovals();
    clearSelected();
  };

  const { error: approveError, dismissError: dismissApproveError } =
    useDismissableError(approveApprovalError);
  const { error: cancelError, dismissError: dismissCancelError } =
    useDismissableError(cancelApprovalError);
  const { error: denyError, dismissError: dismissDenyError } =
    useDismissableError(denyApprovalError);

  const isLoading =
    isWorkflowApprovalsLoading ||
    isDeleteLoading ||
    isApproveLoading ||
    isDenyLoading ||
    isCancelLoading;

  return (
    <>
      <PageSection>
        <Card>
          <PaginatedTable
            contentError={contentError}
            hasContentLoading={isLoading}
            items={workflowApprovals}
            itemCount={count}
            pluralizedItemName={t`Workflow Approvals`}
            qsConfig={QS_CONFIG}
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
                  <WorkflowApprovalControls
                    key="approvalControls"
                    onHandleApprove={handleApprove}
                    selected={selected}
                    onHandleDeny={handleDeny}
                    onHandleCancel={handleCancel}
                    onHandleToggleToolbarKebab={(isOpen) =>
                      setIsKebabModalOpen(isOpen)
                    }
                    isKebabOpen={isKebabOpen}
                  />,
                  <ToolbarDeleteButton
                    key="delete"
                    onDelete={handleDelete}
                    itemsToDelete={selected}
                    pluralizedItemName={t`Workflow Approvals`}
                    cannotDelete={(item) =>
                      item.status === 'pending' ||
                      !item.summary_fields.user_capabilities.delete
                    }
                    errorMessage={
                      <Plural
                        value={selected.length}
                        one="This approval cannot be deleted due to insufficient permissions or a pending job status"
                        other="These approvals cannot be deleted due to insufficient permissions or a pending job status"
                      />
                    }
                  />,
                ]}
              />
            )}
            headerRow={
              <HeaderRow qsConfig={QS_CONFIG}>
                <HeaderCell sortKey="name">{t`Name`}</HeaderCell>
                <HeaderCell>{t`Workflow Job`}</HeaderCell>
                <HeaderCell sortKey="started">{t`Started`}</HeaderCell>
                <HeaderCell>{t`Status`}</HeaderCell>
              </HeaderRow>
            }
            renderRow={(workflowApproval, index) => (
              <WorkflowApprovalListItem
                key={workflowApproval.id}
                workflowApproval={workflowApproval}
                detailUrl={`${match.url}/${workflowApproval.id}`}
                isSelected={selected.some(
                  (row) => row.id === workflowApproval.id
                )}
                onSelect={() => handleSelect(workflowApproval)}
                onSuccessfulAction={fetchWorkflowApprovals}
                rowIndex={index}
              />
            )}
          />
        </Card>
      </PageSection>
      {deletionError && (
        <AlertModal
          isOpen={deletionError}
          variant="error"
          title={t`Error!`}
          onClose={clearDeletionError}
        >
          {t`Failed to delete one or more workflow approval.`}
          <ErrorDetail error={deletionError} />
        </AlertModal>
      )}
      {approveError && (
        <AlertModal
          isOpen={approveError}
          variant="error"
          title={t`Error!`}
          onClose={dismissApproveError}
        >
          {t`Failed to approve one or more workflow approval.`}
          <ErrorDetail error={approveError} />
        </AlertModal>
      )}
      {cancelError && (
        <AlertModal
          isOpen={cancelError}
          variant="error"
          title={t`Error!`}
          onClose={dismissCancelError}
        >
          {t`Failed to cancel one or more workflow approval.`}
          <ErrorDetail error={cancelError} />
        </AlertModal>
      )}
      {denyError && (
        <AlertModal
          isOpen={denyError}
          variant="error"
          title={t`Error!`}
          onClose={dismissDenyError}
        >
          {t`Failed to deny one or more workflow approval.`}
          <ErrorDetail error={denyError} />
        </AlertModal>
      )}
    </>
  );
}

export default WorkflowApprovalsList;
