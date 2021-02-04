import React, { useCallback, useEffect } from 'react';
import { useLocation, useRouteMatch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Card, PageSection } from '@patternfly/react-core';
import { WorkflowApprovalsAPI } from '../../../api';
import PaginatedTable, {
  HeaderRow,
  HeaderCell,
} from '../../../components/PaginatedTable';
import { ToolbarDeleteButton } from '../../../components/PaginatedDataList';
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
    error: actionError,
    dismissError: dismissActionError,
  } = useDismissableError(approveApprovalError || denyApprovalError);

  return (
    <>
      <PageSection>
        <Card>
          <PaginatedTable
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
                key: 'name__icontains',
                isDefault: true,
              },
              {
                name: i18n._(t`Description`),
                key: 'description__icontains',
              },
            ]}
            toolbarSearchableKeys={searchableKeys}
            toolbarRelatedSearchableKeys={relatedSearchableKeys}
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
                    cannotDelete={item =>
                      item.status === 'pending' ||
                      !item.summary_fields.user_capabilities.delete
                    }
                    errorMessage={i18n._(
                      t`These approvals cannot be deleted due to insufficient permissions or a pending job status`
                    )}
                  />,
                ]}
              />
            )}
            headerRow={
              <HeaderRow qsConfig={QS_CONFIG}>
                <HeaderCell sortKey="name">{i18n._(t`Name`)}</HeaderCell>
                <HeaderCell>{i18n._(t`Job`)}</HeaderCell>
                <HeaderCell sortKey="started">{i18n._(t`Started`)}</HeaderCell>
                <HeaderCell>{i18n._(t`Status`)}</HeaderCell>
              </HeaderRow>
            }
            renderRow={(workflowApproval, index) => (
              <WorkflowApprovalListItem
                key={workflowApproval.id}
                workflowApproval={workflowApproval}
                detailUrl={`${match.url}/${workflowApproval.id}`}
                isSelected={selected.some(
                  row => row.id === workflowApproval.id
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
          title={i18n._(t`Error!`)}
          onClose={clearDeletionError}
        >
          {i18n._(t`Failed to delete one or more workflow approval.`)}
          <ErrorDetail error={deletionError} />
        </AlertModal>
      )}
      {actionError && (
        <AlertModal
          isOpen={actionError}
          variant="error"
          title={i18n._(t`Error!`)}
          onClose={dismissActionError}
        >
          {approveApprovalError
            ? i18n._(t`Failed to approve one or more workflow approval.`)
            : i18n._(t`Failed to deny one or more workflow approval.`)}
          <ErrorDetail error={actionError} />
        </AlertModal>
      )}
    </>
  );
}

export default withI18n()(WorkflowApprovalsList);
