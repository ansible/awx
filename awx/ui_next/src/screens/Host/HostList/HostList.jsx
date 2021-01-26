import React, { useState, useEffect, useCallback } from 'react';
import { useHistory, useLocation, useRouteMatch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Card, PageSection } from '@patternfly/react-core';

import { HostsAPI } from '../../../api';
import AlertModal from '../../../components/AlertModal';
import DataListToolbar from '../../../components/DataListToolbar';
import ErrorDetail from '../../../components/ErrorDetail';
import {
  ToolbarAddButton,
  ToolbarDeleteButton,
} from '../../../components/PaginatedDataList';
import PaginatedTable, {
  HeaderRow,
  HeaderCell,
} from '../../../components/PaginatedTable';
import useRequest, { useDeleteItems } from '../../../util/useRequest';
import {
  encodeQueryString,
  getQSConfig,
  parseQueryString,
} from '../../../util/qs';

import HostListItem from './HostListItem';
import SmartInventoryButton from './SmartInventoryButton';

const QS_CONFIG = getQSConfig('host', {
  page: 1,
  page_size: 20,
  order_by: 'name',
});

function HostList({ i18n }) {
  const history = useHistory();
  const location = useLocation();
  const match = useRouteMatch();
  const [selected, setSelected] = useState([]);
  const parsedQueryStrings = parseQueryString(QS_CONFIG, location.search);
  const nonDefaultSearchParams = {};

  Object.keys(parsedQueryStrings).forEach(key => {
    if (!QS_CONFIG.defaultParams[key]) {
      nonDefaultSearchParams[key] = parsedQueryStrings[key];
    }
  });

  const hasNonDefaultSearchParams =
    Object.keys(nonDefaultSearchParams).length > 0;

  const {
    result: { hosts, count, actions, relatedSearchableKeys, searchableKeys },
    error: contentError,
    isLoading,
    request: fetchHosts,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);
      const results = await Promise.all([
        HostsAPI.read(params),
        HostsAPI.readOptions(),
      ]);
      return {
        hosts: results[0].data.results,
        count: results[0].data.count,
        actions: results[1].data.actions,
        relatedSearchableKeys: (
          results[1]?.data?.related_search_fields || []
        ).map(val => val.slice(0, -8)),
        searchableKeys: Object.keys(results[1].data.actions?.GET || {}).filter(
          key => results[1].data.actions?.GET[key].filterable
        ),
      };
    }, [location]),
    {
      hosts: [],
      count: 0,
      actions: {},
      relatedSearchableKeys: [],
      searchableKeys: [],
    }
  );

  useEffect(() => {
    fetchHosts();
  }, [fetchHosts]);

  const isAllSelected = selected.length === hosts.length && selected.length > 0;
  const {
    isLoading: isDeleteLoading,
    deleteItems: deleteHosts,
    deletionError,
    clearDeletionError,
  } = useDeleteItems(
    useCallback(() => {
      return Promise.all(selected.map(host => HostsAPI.destroy(host.id)));
    }, [selected]),
    {
      qsConfig: QS_CONFIG,
      allItemsSelected: isAllSelected,
      fetchItems: fetchHosts,
    }
  );

  const handleHostDelete = async () => {
    await deleteHosts();
    setSelected([]);
  };

  const handleSelectAll = isSelected => {
    setSelected(isSelected ? [...hosts] : []);
  };

  const handleSelect = host => {
    if (selected.some(h => h.id === host.id)) {
      setSelected(selected.filter(h => h.id !== host.id));
    } else {
      setSelected(selected.concat(host));
    }
  };

  const handleSmartInventoryClick = () => {
    history.push(
      `/inventories/smart_inventory/add?host_filter=${encodeURIComponent(
        encodeQueryString(nonDefaultSearchParams)
      )}`
    );
  };

  const canAdd =
    actions && Object.prototype.hasOwnProperty.call(actions, 'POST');

  return (
    <PageSection>
      <Card>
        <PaginatedTable
          contentError={contentError}
          hasContentLoading={isLoading || isDeleteLoading}
          items={hosts}
          itemCount={count}
          pluralizedItemName={i18n._(t`Hosts`)}
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
            {
              name: i18n._(t`Created By (Username)`),
              key: 'created_by__username__icontains',
            },
            {
              name: i18n._(t`Modified By (Username)`),
              key: 'modified_by__username__icontains',
            },
          ]}
          toolbarSearchableKeys={searchableKeys}
          toolbarRelatedSearchableKeys={relatedSearchableKeys}
          headerRow={
            <HeaderRow qsConfig={QS_CONFIG}>
              <HeaderCell sortKey="name">{i18n._(t`Name`)}</HeaderCell>
              <HeaderCell>{i18n._(t`Inventory`)}</HeaderCell>
            </HeaderRow>
          }
          renderToolbar={props => (
            <DataListToolbar
              {...props}
              showSelectAll
              isAllSelected={isAllSelected}
              onSelectAll={handleSelectAll}
              qsConfig={QS_CONFIG}
              additionalControls={[
                ...(canAdd
                  ? [<ToolbarAddButton key="add" linkTo={`${match.url}/add`} />]
                  : []),
                <ToolbarDeleteButton
                  key="delete"
                  onDelete={handleHostDelete}
                  itemsToDelete={selected}
                  pluralizedItemName={i18n._(t`Hosts`)}
                />,
                ...(canAdd
                  ? [
                      <SmartInventoryButton
                        isDisabled={!hasNonDefaultSearchParams}
                        onClick={() => handleSmartInventoryClick()}
                      />,
                    ]
                  : []),
              ]}
            />
          )}
          renderRow={(host, index) => (
            <HostListItem
              key={host.id}
              host={host}
              detailUrl={`${match.url}/${host.id}/details`}
              isSelected={selected.some(row => row.id === host.id)}
              onSelect={() => handleSelect(host)}
              rowIndex={index}
            />
          )}
          emptyStateControls={
            canAdd ? (
              <ToolbarAddButton key="add" linkTo={`${match.url}/add`} />
            ) : null
          }
        />
      </Card>
      {deletionError && (
        <AlertModal
          isOpen={deletionError}
          variant="error"
          title={i18n._(t`Error!`)}
          onClose={clearDeletionError}
        >
          {i18n._(t`Failed to delete one or more hosts.`)}
          <ErrorDetail error={deletionError} />
        </AlertModal>
      )}
    </PageSection>
  );
}

export default withI18n()(HostList);
