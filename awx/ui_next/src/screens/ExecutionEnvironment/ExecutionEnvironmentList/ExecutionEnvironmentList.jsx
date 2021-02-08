import React, { useEffect, useCallback } from 'react';
import { useLocation, useRouteMatch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Card, PageSection } from '@patternfly/react-core';

import { ExecutionEnvironmentsAPI } from '../../../api';
import { getQSConfig, parseQueryString } from '../../../util/qs';
import useRequest, { useDeleteItems } from '../../../util/useRequest';
import useSelected from '../../../util/useSelected';
import {
  ToolbarDeleteButton,
  ToolbarAddButton,
} from '../../../components/PaginatedDataList';
import PaginatedTable, {
  HeaderRow,
  HeaderCell,
} from '../../../components/PaginatedTable';
import ErrorDetail from '../../../components/ErrorDetail';
import AlertModal from '../../../components/AlertModal';
import DatalistToolbar from '../../../components/DataListToolbar';

import ExecutionEnvironmentsListItem from './ExecutionEnvironmentListItem';

const QS_CONFIG = getQSConfig('execution_environments', {
  page: 1,
  page_size: 20,
  order_by: 'name',
});

function ExecutionEnvironmentList({ i18n }) {
  const location = useLocation();
  const match = useRouteMatch();

  const {
    error: contentError,
    isLoading,
    request: fetchExecutionEnvironments,
    result: {
      executionEnvironments,
      executionEnvironmentsCount,
      actions,
      relatedSearchableKeys,
      searchableKeys,
    },
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);

      const [response, responseActions] = await Promise.all([
        ExecutionEnvironmentsAPI.read(params),
        ExecutionEnvironmentsAPI.readOptions(),
      ]);

      return {
        executionEnvironments: response.data.results,
        executionEnvironmentsCount: response.data.count,
        actions: responseActions.data.actions,
        relatedSearchableKeys: (
          responseActions?.data?.related_search_fields || []
        ).map(val => val.slice(0, -8)),
        searchableKeys: Object.keys(
          responseActions.data.actions?.GET || {}
        ).filter(key => responseActions.data.actions?.GET[key].filterable),
      };
    }, [location]),
    {
      executionEnvironments: [],
      executionEnvironmentsCount: 0,
      actions: {},
      relatedSearchableKeys: [],
      searchableKeys: [],
    }
  );

  useEffect(() => {
    fetchExecutionEnvironments();
  }, [fetchExecutionEnvironments]);

  const { selected, isAllSelected, handleSelect, setSelected } = useSelected(
    executionEnvironments
  );

  const {
    isLoading: deleteLoading,
    deletionError,
    deleteItems: deleteExecutionEnvironments,
    clearDeletionError,
  } = useDeleteItems(
    useCallback(async () => {
      await Promise.all(
        selected.map(({ id }) => ExecutionEnvironmentsAPI.destroy(id))
      );
    }, [selected]),
    {
      qsConfig: QS_CONFIG,
      allItemsSelected: isAllSelected,
      fetchItems: fetchExecutionEnvironments,
    }
  );

  const handleDelete = async () => {
    await deleteExecutionEnvironments();
    setSelected([]);
  };

  const canAdd = actions && actions.POST;

  return (
    <>
      <PageSection>
        <Card>
          <PaginatedTable
            contentError={contentError}
            hasContentLoading={isLoading || deleteLoading}
            items={executionEnvironments}
            itemCount={executionEnvironmentsCount}
            pluralizedItemName={i18n._(t`Execution Environments`)}
            qsConfig={QS_CONFIG}
            onRowClick={handleSelect}
            toolbarSearchableKeys={searchableKeys}
            toolbarRelatedSearchableKeys={relatedSearchableKeys}
            toolbarSearchColumns={[
              {
                name: i18n._(t`Image`),
                key: 'image__icontains',
                isDefault: true,
              },
            ]}
            toolbarSortColumns={[
              {
                name: i18n._(t`Image`),
                key: 'image',
              },
              {
                name: i18n._(t`Created`),
                key: 'created',
              },
              {
                name: i18n._(t`Organization`),
                key: 'organization',
              },
              {
                name: i18n._(t`Description`),
                key: 'description',
              },
            ]}
            headerRow={
              <HeaderRow qsConfig={QS_CONFIG}>
                <HeaderCell sortKey="name">{i18n._(t`Name`)}</HeaderCell>
                <HeaderCell>{i18n._(t`Image`)}</HeaderCell>
                <HeaderCell>{i18n._(t`Organization`)}</HeaderCell>
              </HeaderRow>
            }
            renderToolbar={props => (
              <DatalistToolbar
                {...props}
                showSelectAll
                isAllSelected={isAllSelected}
                onSelectAll={isSelected =>
                  setSelected(isSelected ? [...executionEnvironments] : [])
                }
                qsConfig={QS_CONFIG}
                additionalControls={[
                  ...(canAdd
                    ? [
                        <ToolbarAddButton
                          key="add"
                          linkTo={`${match.url}/add`}
                        />,
                      ]
                    : []),
                  <ToolbarDeleteButton
                    key="delete"
                    onDelete={handleDelete}
                    itemsToDelete={selected}
                    pluralizedItemName={i18n._(t`Execution Environments`)}
                  />,
                ]}
              />
            )}
            renderRow={(executionEnvironment, index) => (
              <ExecutionEnvironmentsListItem
                key={executionEnvironment.id}
                rowIndex={index}
                executionEnvironment={executionEnvironment}
                detailUrl={`${match.url}/${executionEnvironment.id}/details`}
                onSelect={() => handleSelect(executionEnvironment)}
                isSelected={selected.some(
                  row => row.id === executionEnvironment.id
                )}
              />
            )}
            emptyStateControls={
              canAdd && (
                <ToolbarAddButton key="add" linkTo={`${match.url}/add`} />
              )
            }
          />
        </Card>
      </PageSection>
      <AlertModal
        aria-label={i18n._(t`Deletion error`)}
        isOpen={deletionError}
        onClose={clearDeletionError}
        title={i18n._(t`Error`)}
        variant="error"
      >
        {i18n._(t`Failed to delete one or more execution environments`)}
        <ErrorDetail error={deletionError} />
      </AlertModal>
    </>
  );
}

export default withI18n()(ExecutionEnvironmentList);
