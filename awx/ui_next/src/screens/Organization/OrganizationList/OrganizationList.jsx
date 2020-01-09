import React, { useEffect, useState } from 'react';
import { useLocation, useRouteMatch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Card, PageSection } from '@patternfly/react-core';

import { OrganizationsAPI } from '@api';
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
  const [contentError, setContentError] = useState(null);
  const [deletionError, setDeletionError] = useState(null);
  const [hasContentLoading, setHasContentLoading] = useState(true);
  const [itemCount, setItemCount] = useState(0);
  const [organizations, setOrganizations] = useState([]);
  const [orgActions, setOrgActions] = useState(null);
  const [selected, setSelected] = useState([]);

  const addUrl = `${match.url}/add`;
  const canAdd = orgActions && orgActions.POST;
  const isAllSelected =
    selected.length === organizations.length && selected.length > 0;

  const loadOrganizations = async ({ search }) => {
    const params = parseQueryString(QS_CONFIG, search);
    setContentError(null);
    setHasContentLoading(true);
    try {
      const [
        {
          data: { count, results },
        },
        {
          data: { actions },
        },
      ] = await Promise.all([
        OrganizationsAPI.read(params),
        loadOrganizationActions(),
      ]);
      setItemCount(count);
      setOrganizations(results);
      setOrgActions(actions);
      setSelected([]);
    } catch (error) {
      setContentError(error);
    } finally {
      setHasContentLoading(false);
    }
  };

  const loadOrganizationActions = () => {
    if (orgActions) {
      return Promise.resolve({ data: { actions: orgActions } });
    }
    return OrganizationsAPI.readOptions();
  };

  const handleOrgDelete = async () => {
    setHasContentLoading(true);
    try {
      await Promise.all(selected.map(({ id }) => OrganizationsAPI.destroy(id)));
    } catch (error) {
      setDeletionError(error);
    } finally {
      await loadOrganizations(location);
    }
  };

  const handleSelectAll = isSelected => {
    if (isSelected) {
      setSelected(organizations);
    } else {
      setSelected([]);
    }
  };

  const handleSelect = row => {
    if (selected.some(s => s.id === row.id)) {
      setSelected(selected.filter(s => s.id !== row.id));
    } else {
      setSelected(selected.concat(row));
    }
  };

  const handleDeleteErrorClose = () => {
    setDeletionError(null);
  };

  useEffect(() => {
    loadOrganizations(location);
  }, [location]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <>
      <PageSection>
        <Card>
          <PaginatedDataList
            contentError={contentError}
            hasContentLoading={hasContentLoading}
            items={organizations}
            itemCount={itemCount}
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
                  <ToolbarDeleteButton
                    key="delete"
                    onDelete={handleOrgDelete}
                    itemsToDelete={selected}
                    pluralizedItemName="Organizations"
                  />,
                  canAdd ? (
                    <ToolbarAddButton key="add" linkTo={addUrl} />
                  ) : null,
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
        variant="danger"
        title={i18n._(t`Error!`)}
        onClose={handleDeleteErrorClose}
      >
        {i18n._(t`Failed to delete one or more organizations.`)}
        <ErrorDetail error={deletionError} />
      </AlertModal>
    </>
  );
}

export { OrganizationsList as _OrganizationsList };
export default withI18n()(OrganizationsList);
