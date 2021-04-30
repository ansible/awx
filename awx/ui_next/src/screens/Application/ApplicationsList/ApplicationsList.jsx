import React, { useCallback, useEffect } from 'react';
import { t } from '@lingui/macro';

import { useLocation, useRouteMatch } from 'react-router-dom';

import { Card, PageSection } from '@patternfly/react-core';
import { getQSConfig, parseQueryString } from '../../../util/qs';
import useRequest, { useDeleteItems } from '../../../util/useRequest';
import ErrorDetail from '../../../components/ErrorDetail';
import AlertModal from '../../../components/AlertModal';

import DatalistToolbar from '../../../components/DataListToolbar';
import { ApplicationsAPI } from '../../../api';
import PaginatedTable, {
  HeaderRow,
  HeaderCell,
} from '../../../components/PaginatedTable';
import {
  ToolbarDeleteButton,
  ToolbarAddButton,
} from '../../../components/PaginatedDataList';
import useSelected from '../../../util/useSelected';

import ApplicationListItem from './ApplicationListItem';

const QS_CONFIG = getQSConfig('applications', {
  page: 1,
  page_size: 20,
  order_by: 'name',
});
function ApplicationsList() {
  const location = useLocation();
  const match = useRouteMatch();

  const {
    isLoading,
    error,
    request: fetchApplications,
    result: {
      applications,
      itemCount,
      actions,
      relatedSearchableKeys,
      searchableKeys,
    },
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);

      const [response, actionsResponse] = await Promise.all([
        ApplicationsAPI.read(params),
        ApplicationsAPI.readOptions(),
      ]);

      return {
        applications: response.data.results,
        itemCount: response.data.count,
        actions: actionsResponse.data.actions,
        relatedSearchableKeys: (
          actionsResponse?.data?.related_search_fields || []
        ).map(val => val.slice(0, -8)),
        searchableKeys: Object.keys(
          actionsResponse.data.actions?.GET || {}
        ).filter(key => actionsResponse.data.actions?.GET[key].filterable),
      };
    }, [location]),
    {
      applications: [],
      itemCount: 0,
      actions: {},
      relatedSearchableKeys: [],
      searchableKeys: [],
    }
  );

  useEffect(() => {
    fetchApplications();
  }, [fetchApplications]);

  const { selected, isAllSelected, handleSelect, setSelected } = useSelected(
    applications
  );

  const {
    isLoading: deleteLoading,
    deletionError,
    deleteItems: deleteApplications,
    clearDeletionError,
  } = useDeleteItems(
    useCallback(() => {
      return Promise.all(selected.map(({ id }) => ApplicationsAPI.destroy(id)));
    }, [selected]),
    {
      qsConfig: QS_CONFIG,
      allItemsSelected: isAllSelected,
      fetchItems: fetchApplications,
    }
  );

  const handleDeleteApplications = async () => {
    await deleteApplications();
    setSelected([]);
  };

  const canAdd = actions && actions.POST;

  return (
    <>
      <PageSection>
        <Card>
          <PaginatedTable
            contentError={error}
            hasContentLoading={isLoading || deleteLoading}
            items={applications}
            itemCount={itemCount}
            pluralizedItemName={t`Applications`}
            qsConfig={QS_CONFIG}
            onRowClick={handleSelect}
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
            renderToolbar={props => (
              <DatalistToolbar
                {...props}
                showSelectAll
                isAllSelected={isAllSelected}
                onSelectAll={isSelected =>
                  setSelected(isSelected ? [...applications] : [])
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
                    onDelete={handleDeleteApplications}
                    itemsToDelete={selected}
                    pluralizedItemName={t`Applications`}
                  />,
                ]}
              />
            )}
            headerRow={
              <HeaderRow qsConfig={QS_CONFIG}>
                <HeaderCell sortKey="name">{t`Name`}</HeaderCell>
                <HeaderCell sortKey="organization">
                  {t`Organization`}
                </HeaderCell>
                <HeaderCell>{t`Last Modified`}</HeaderCell>
                <HeaderCell>{t`Actions`}</HeaderCell>
              </HeaderRow>
            }
            renderRow={(application, index) => (
              <ApplicationListItem
                key={application.id}
                value={application.name}
                application={application}
                detailUrl={`${match.url}/${application.id}/details`}
                onSelect={() => handleSelect(application)}
                isSelected={selected.some(row => row.id === application.id)}
                rowIndex={index}
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
        isOpen={deletionError}
        variant="error"
        title={t`Error!`}
        onClose={clearDeletionError}
      >
        {t`Failed to delete one or more applications.`}
        <ErrorDetail error={deletionError} />
      </AlertModal>
    </>
  );
}
export default ApplicationsList;
