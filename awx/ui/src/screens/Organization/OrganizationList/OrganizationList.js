import React, { useEffect, useCallback } from 'react';
import { useLocation, useRouteMatch } from 'react-router-dom';
import { t, Plural } from '@lingui/macro';
import { Card, PageSection } from '@patternfly/react-core';

import { OrganizationsAPI } from 'api';
import useRequest, { useDeleteItems } from 'hooks/useRequest';
import AlertModal from 'components/AlertModal';
import DataListToolbar from 'components/DataListToolbar';
import ErrorDetail from 'components/ErrorDetail';
import PaginatedTable, {
  HeaderRow,
  HeaderCell,
  ToolbarAddButton,
  ToolbarDeleteButton,
  getSearchableKeys,
} from 'components/PaginatedTable';
import { getQSConfig, parseQueryString } from 'util/qs';
import useSelected from 'hooks/useSelected';
import { relatedResourceDeleteRequests } from 'util/getRelatedResourceDeleteDetails';
import OrganizationListItem from './OrganizationListItem';

const QS_CONFIG = getQSConfig('organization', {
  page: 1,
  page_size: 20,
  order_by: 'name',
});

function OrganizationsList() {
  const location = useLocation();
  const match = useRouteMatch();

  const addUrl = `${match.url}/add`;

  const {
    result: {
      organizations,
      organizationCount,
      actions,
      relatedSearchableKeys,
      searchableKeys,
    },
    error: contentError,
    isLoading: isOrgsLoading,
    request: fetchOrganizations,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);
      const [orgs, orgActions] = await Promise.all([
        OrganizationsAPI.read(params),
        OrganizationsAPI.readOptions(),
      ]);
      return {
        organizations: orgs.data.results,
        organizationCount: orgs.data.count,
        actions: orgActions.data.actions,
        relatedSearchableKeys: (
          orgActions?.data?.related_search_fields || []
        ).map((val) => val.slice(0, -8)),
        searchableKeys: getSearchableKeys(orgActions.data.actions?.GET),
      };
    }, [location]),
    {
      organizations: [],
      organizationCount: 0,
      actions: {},
      relatedSearchableKeys: [],
      searchableKeys: [],
    }
  );

  useEffect(() => {
    fetchOrganizations();
  }, [fetchOrganizations]);

  const { selected, isAllSelected, handleSelect, selectAll, clearSelected } =
    useSelected(organizations);

  const {
    isLoading: isDeleteLoading,
    deleteItems: deleteOrganizations,
    deletionError,
    clearDeletionError,
  } = useDeleteItems(
    useCallback(
      () => Promise.all(selected.map(({ id }) => OrganizationsAPI.destroy(id))),
      [selected]
    ),
    {
      qsConfig: QS_CONFIG,
      allItemsSelected: isAllSelected,
      fetchItems: fetchOrganizations,
    }
  );

  const handleOrgDelete = async () => {
    await deleteOrganizations();
    clearSelected();
  };

  const hasContentLoading = isDeleteLoading || isOrgsLoading;
  const canAdd = actions && actions.POST;

  const deleteDetailsRequests = relatedResourceDeleteRequests.organization(
    selected[0]
  );

  return (
    <>
      <PageSection>
        <Card>
          <PaginatedTable
            contentError={contentError}
            hasContentLoading={hasContentLoading}
            items={organizations}
            itemCount={organizationCount}
            pluralizedItemName={t`Organizations`}
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
              {
                name: t`Created By (Username)`,
                key: 'created_by__username__icontains',
              },
              {
                name: t`Modified By (Username)`,
                key: 'modified_by__username__icontains',
              },
            ]}
            toolbarSearchableKeys={searchableKeys}
            toolbarRelatedSearchableKeys={relatedSearchableKeys}
            headerRow={
              <HeaderRow qsConfig={QS_CONFIG}>
                <HeaderCell sortKey="name">{t`Name`}</HeaderCell>
                <HeaderCell>{t`Members`}</HeaderCell>
                <HeaderCell>{t`Teams`}</HeaderCell>
                <HeaderCell>{t`Actions`}</HeaderCell>
              </HeaderRow>
            }
            renderToolbar={(props) => (
              <DataListToolbar
                {...props}
                isAllSelected={isAllSelected}
                onSelectAll={selectAll}
                qsConfig={QS_CONFIG}
                additionalControls={[
                  ...(canAdd
                    ? [<ToolbarAddButton key="add" linkTo={addUrl} />]
                    : []),
                  <ToolbarDeleteButton
                    key="delete"
                    onDelete={handleOrgDelete}
                    itemsToDelete={selected}
                    pluralizedItemName={t`Organizations`}
                    deleteDetailsRequests={deleteDetailsRequests}
                    deleteMessage={
                      <Plural
                        value={selected.length}
                        one="This organization is currently being used by other resources. Are you sure you want to delete it?"
                        other="Deleting these organizations could impact other resources that rely on them. Are you sure you want to delete anyway?"
                      />
                    }
                  />,
                ]}
              />
            )}
            renderRow={(o, index) => (
              <OrganizationListItem
                key={o.id}
                organization={o}
                rowIndex={index}
                detailUrl={`${match.url}/${o.id}`}
                isSelected={selected.some((row) => row.id === o.id)}
                onSelect={() => handleSelect(o)}
              />
            )}
            emptyStateControls={
              canAdd ? <ToolbarAddButton key="add" linkTo={addUrl} /> : null
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
        {t`Failed to delete one or more organizations.`}
        <ErrorDetail error={deletionError} />
      </AlertModal>
    </>
  );
}

export { OrganizationsList as _OrganizationsList };
export default OrganizationsList;
