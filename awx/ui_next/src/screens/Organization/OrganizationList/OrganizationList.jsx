import React, { useState, useEffect, useCallback } from 'react';
import { useLocation, useRouteMatch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Card, PageSection } from '@patternfly/react-core';

import { OrganizationsAPI } from '@api';
import useRequest, { useDeleteItems } from '@util/useRequest';
import AlertModal from '@components/AlertModal';
import DataListToolbar from '@components/DataListToolbar';
import ErrorDetail from '@components/ErrorDetail';
import PaginatedDataList, {
  ToolbarAddButton,
  ToolbarDeleteButton,
} from '@components/PaginatedDataList';
import { getQSConfig, parseQueryString } from '@util/qs';
import OrganizationListItem from './OrganizationListItem';

const QS_CONFIG = getQSConfig('organization', {
  page: 1,
  page_size: 20,
  order_by: 'name',
});

function OrganizationsList({ i18n }) {
  const location = useLocation();
  const match = useRouteMatch();

  const [selected, setSelected] = useState([]);

  const addUrl = `${match.url}/add`;

  const {
    result: { organizations, organizationCount, actions },
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
      };
    }, [location]),
    {
      organizations: [],
      organizationCount: 0,
      actions: {},
    }
  );

  useEffect(() => {
    fetchOrganizations();
  }, [fetchOrganizations]);

  const isAllSelected =
    selected.length === organizations.length && selected.length > 0;
  const {
    isLoading: isDeleteLoading,
    deleteItems: deleteOrganizations,
    deletionError,
    clearDeletionError,
  } = useDeleteItems(
    useCallback(async () => {
      return Promise.all(
        selected.map(({ id }) => OrganizationsAPI.destroy(id))
      );
    }, [selected]),
    {
      qsConfig: QS_CONFIG,
      allItemsSelected: isAllSelected,
      fetchItems: fetchOrganizations,
    }
  );

  const handleOrgDelete = async () => {
    await deleteOrganizations();
    setSelected([]);
  };

  const hasContentLoading = isDeleteLoading || isOrgsLoading;
  const canAdd = actions && actions.POST;

  const handleSelectAll = isSelected => {
    setSelected(isSelected ? [...organizations] : []);
  };

  const handleSelect = row => {
    if (selected.some(s => s.id === row.id)) {
      setSelected(selected.filter(s => s.id !== row.id));
    } else {
      setSelected(selected.concat(row));
    }
  };

  return (
    <>
      <PageSection>
        <Card>
          <PaginatedDataList
            contentError={contentError}
            hasContentLoading={hasContentLoading}
            items={organizations}
            itemCount={organizationCount}
            pluralizedItemName="Organizations"
            qsConfig={QS_CONFIG}
            onRowClick={handleSelect}
            toolbarSearchColumns={[
              {
                name: i18n._(t`Name`),
                key: 'name',
                isDefault: true,
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
                name: i18n._(t`Name`),
                key: 'name',
              },
            ]}
            renderToolbar={props => (
              <DataListToolbar
                {...props}
                showSelectAll
                isAllSelected={isAllSelected}
                onSelectAll={handleSelectAll}
                qsConfig={QS_CONFIG}
                additionalControls={[
                  ...(canAdd
                    ? [<ToolbarAddButton key="add" linkTo={addUrl} />]
                    : []),
                  <ToolbarDeleteButton
                    key="delete"
                    onDelete={handleOrgDelete}
                    itemsToDelete={selected}
                    pluralizedItemName="Organizations"
                  />,
                ]}
              />
            )}
            renderItem={o => (
              <OrganizationListItem
                key={o.id}
                organization={o}
                detailUrl={`${match.url}/${o.id}`}
                isSelected={selected.some(row => row.id === o.id)}
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
        title={i18n._(t`Error!`)}
        onClose={clearDeletionError}
      >
        {i18n._(t`Failed to delete one or more organizations.`)}
        <ErrorDetail error={deletionError} />
      </AlertModal>
    </>
  );
}

export { OrganizationsList as _OrganizationsList };
export default withI18n()(OrganizationsList);
