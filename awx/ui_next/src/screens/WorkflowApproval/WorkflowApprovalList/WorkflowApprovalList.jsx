import React, { useCallback, useEffect } from 'react';
import { useLocation, useRouteMatch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Card, PageSection } from '@patternfly/react-core';
import { WorkflowApprovalsAPI } from '../../../api';
import PaginatedDataList, {
  ToolbarDeleteButton,
} from '../../../components/PaginatedDataList';
import AlertModal from '../../../components/AlertModal';
import ErrorDetail from '../../../components/ErrorDetail';
import DataListToolbar from '../../../components/DataListToolbar';
import WorkflowApprovalListItem from './WorkflowApprovalListItem';
import useRequest, {
  useDeleteItems,
  useDismissableError,
} from '../../../util/useRequest';
import useSelected from '../../../util/useSelected';
import { getQSConfig, parseQueryString } from '../../../util/qs';
import useWsWorkflowApprovals from './useWsWorkflowApprovals';
import WorkflowApprovalListApproveButton from './WorkflowApprovalListApproveButton';
import WorkflowApprovalListDenyButton from './WorkflowApprovalListDenyButton';

const QS_CONFIG = getQSConfig('workflow_approvals', {
  page: 1,
  page_size: 20,
  order_by: '-started',
});

function WorkflowApprovalsList({ i18n }) {
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
        ).map(val => val.slice(0, -8)),
        searchableKeys: Object.keys(
          actionsResponse.data.actions?.GET || {}
        ).filter(key => actionsResponse.data.actions?.GET[key].filterable),
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

  // TODO: update QS_CONFIG to be safe for deps array
  const fetchWorkflowApprovalsById = useCallback(
    async ids => {
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

  const { selected, isAllSelected, handleSelect, setSelected } = useSelected(
    workflowApprovals
  );

  const {
    isLoading: isDeleteLoading,
    deleteItems: deleteWorkflowApprovals,
    deletionError,
    clearDeletionError,
  } = useDeleteItems(
    useCallback(async () => {
      return Promise.all(
        selected.map(({ id }) => WorkflowApprovalsAPI.destroy(id))
      );
    }, [selected]),
    {
      qsConfig: QS_CONFIG,
      allItemsSelected: isAllSelected,
      fetchItems: fetchWorkflowApprovals,
    }
  );

  const handleDelete = async () => {
    await deleteWorkflowApprovals();
    setSelected([]);
  };

  const {
    error: approveApprovalError,
    isLoading: isApproveLoading,
    request: approveWorkflowApprovals,
  } = useRequest(
    useCallback(async () => {
      return Promise.all(
        selected.map(({ id }) => WorkflowApprovalsAPI.approve(id))
      );
    }, [selected]),
    {}
  );

  const handleApprove = async () => {
    await approveWorkflowApprovals();
    setSelected([]);
  };

  const {
    error: approveError,
    dismissError: dismissApproveError,
  } = useDismissableError(approveApprovalError);

  const {
    error: denyApprovalError,
    isLoading: isDenyLoading,
    request: denyWorkflowApprovals,
  } = useRequest(
    useCallback(async () => {
      return Promise.all(
        selected.map(({ id }) => WorkflowApprovalsAPI.deny(id))
      );
    }, [selected]),
    {}
  );

  const handleDeny = async () => {
    await denyWorkflowApprovals();
    setSelected([]);
  };

  const {
    error: denyError,
    dismissError: dismissDenyError,
  } = useDismissableError(denyApprovalError);

  return (
    <>
      <PageSection>
        <Card>
          <PaginatedDataList
            contentError={contentError}
            hasContentLoading={
              isWorkflowApprovalsLoading ||
              isDeleteLoading ||
              isApproveLoading ||
              isDenyLoading
            }
            items={workflowApprovals}
            itemCount={count}
            pluralizedItemName={i18n._(t`Workflow Approvals`)}
            qsConfig={QS_CONFIG}
            onRowClick={handleSelect}
            toolbarSearchColumns={[
              {
                name: i18n._(t`Name`),
                key: 'name',
                isDefault: true,
              },
            ]}
            toolbarSearchableKeys={searchableKeys}
            toolbarRelatedSearchableKeys={relatedSearchableKeys}
            toolbarSortColumns={[
              {
                name: i18n._(t`Name`),
                key: 'name',
              },
              {
                name: i18n._(t`Started`),
                key: 'started',
              },
            ]}
            renderToolbar={props => (
              <DataListToolbar
                {...props}
                showSelectAll
                isAllSelected={isAllSelected}
                onSelectAll={set =>
                  setSelected(set ? [...workflowApprovals] : [])
                }
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
                    pluralizedItemName={i18n._(t`Workflow Approvals`)}
                  />,
                ]}
              />
            )}
            renderItem={workflowApproval => (
              <WorkflowApprovalListItem
                key={workflowApproval.id}
                workflowApproval={workflowApproval}
                detailUrl={`${match.url}/${workflowApproval.id}`}
                isSelected={selected.some(
                  row => row.id === workflowApproval.id
                )}
                onSelect={() => handleSelect(workflowApproval)}
                onSuccessfulAction={fetchWorkflowApprovals}
              />
            )}
          />
        </Card>
      </PageSection>
      {deletionError && (
        <AlertModal
          isOpen={deletionError}
          variant="error"
          title={i18n._(t`Error!`)}
          onClose={clearDeletionError}
        >
          {i18n._(t`Failed to delete one or more workflow approval.`)}
          <ErrorDetail error={deletionError} />
        </AlertModal>
      )}
      {approveError && (
        <AlertModal
          isOpen={approveError}
          variant="error"
          title={i18n._(t`Error!`)}
          onClose={dismissApproveError}
        >
          {i18n._(t`Failed to approve one or more workflow approval.`)}
          <ErrorDetail error={approveError} />
        </AlertModal>
      )}
      {denyError && (
        <AlertModal
          isOpen={denyError}
          variant="error"
          title={i18n._(t`Error!`)}
          onClose={dismissDenyError}
        >
          {i18n._(t`Failed to deny one or more workflow approval.`)}
          <ErrorDetail error={denyError} />
        </AlertModal>
      )}
    </>
  );
}

export default withI18n()(WorkflowApprovalsList);
