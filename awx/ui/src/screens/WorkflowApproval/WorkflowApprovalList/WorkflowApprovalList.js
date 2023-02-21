import React, { useCallback, useEffect } from 'react';
import { useLocation, useRouteMatch } from 'react-router-dom';
import { t, Plural } from '@lingui/macro';
import { Card, PageSection } from '@patternfly/react-core';
import { WorkflowApprovalsAPI } from 'api';
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
import WorkflowApprovalListApproveButton from './WorkflowApprovalListApproveButton';
import WorkflowApprovalListDenyButton from './WorkflowApprovalListDenyButton';

const QS_CONFIG = getQSConfig('workflow_approvals', {
  page: 1,
  page_size: 20,
  order_by: '-started',
});

function WorkflowApprovalsList() {
  const location = useLocation();
  const match = useRouteMatch();

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
      return {
        results: response.data.results,
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
    await denyWorkflowApprovals();
    clearSelected();
  };

  const { error: actionError, dismissError: dismissActionError } =
    useDismissableError(approveApprovalError || denyApprovalError);

  const isLoading =
    isWorkflowApprovalsLoading ||
    isDeleteLoading ||
    isApproveLoading ||
    isDenyLoading;

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
                  <WorkflowApprovalListApproveButton
                    key="approve"
                    onApprove={handleApprove}
                    selectedItems={selected}
                  />,
                  <WorkflowApprovalListDenyButton
                    key="deny"
                    onDeny={handleDeny}
                    selectedItems={selected}
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
                <HeaderCell>{t`Actions`}</HeaderCell>
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
      {actionError && (
        <AlertModal
          isOpen={actionError}
          variant="error"
          title={t`Error!`}
          onClose={dismissActionError}
        >
          {approveApprovalError
            ? t`Failed to approve one or more workflow approval.`
            : t`Failed to deny one or more workflow approval.`}
          <ErrorDetail error={actionError} />
        </AlertModal>
      )}
    </>
  );
}

export default WorkflowApprovalsList;
