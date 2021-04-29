import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useLocation } from 'react-router-dom';
import { t } from '@lingui/macro';
import { getQSConfig, parseQueryString } from '../../../util/qs';
import { InventoriesAPI, HostsAPI } from '../../../api';
import useRequest, { useDeleteItems } from '../../../util/useRequest';
import AlertModal from '../../../components/AlertModal';
import DataListToolbar from '../../../components/DataListToolbar';
import ErrorDetail from '../../../components/ErrorDetail';
import PaginatedTable, {
  HeaderRow,
  HeaderCell,
} from '../../../components/PaginatedTable';
import {
  ToolbarAddButton,
  ToolbarDeleteButton,
} from '../../../components/PaginatedDataList';
import AdHocCommands from '../../../components/AdHocCommands/AdHocCommands';
import InventoryHostItem from './InventoryHostItem';

const QS_CONFIG = getQSConfig('host', {
  page: 1,
  page_size: 20,
  order_by: 'name',
});

function InventoryHostList() {
  const [selected, setSelected] = useState([]);
  const [isAdHocLaunchLoading, setIsAdHocLaunchLoading] = useState(false);
  const { id } = useParams();
  const { search } = useLocation();

  const {
    result: {
      hosts,
      hostCount,
      actions,
      relatedSearchableKeys,
      searchableKeys,
    },
    error: contentError,
    isLoading,
    request: fetchData,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, search);
      const [response, hostOptions] = await Promise.all([
        InventoriesAPI.readHosts(id, params),
        InventoriesAPI.readHostsOptions(id),
      ]);

      return {
        hosts: response.data.results,
        hostCount: response.data.count,
        actions: hostOptions.data.actions,
        relatedSearchableKeys: (
          hostOptions?.data?.related_search_fields || []
        ).map(val => val.slice(0, -8)),
        searchableKeys: Object.keys(hostOptions.data.actions?.GET || {}).filter(
          key => hostOptions.data.actions?.GET[key].filterable
        ),
      };
    }, [id, search]),
    {
      hosts: [],
      hostCount: 0,
      actions: {},
      relatedSearchableKeys: [],
      searchableKeys: [],
    }
  );

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleSelectAll = isSelected => {
    setSelected(isSelected ? [...hosts] : []);
  };

  const handleSelect = row => {
    if (selected.some(s => s.id === row.id)) {
      setSelected(selected.filter(s => s.id !== row.id));
    } else {
      setSelected(selected.concat(row));
    }
  };
  const {
    isLoading: isDeleteLoading,
    deleteItems: deleteHosts,
    deletionError,
    clearDeletionError,
  } = useDeleteItems(
    useCallback(() => {
      return Promise.all(selected.map(host => HostsAPI.destroy(host.id)));
    }, [selected]),
    { qsConfig: QS_CONFIG, fetchItems: fetchData }
  );

  const handleDeleteHosts = async () => {
    await deleteHosts();
    setSelected([]);
  };

  const canAdd =
    actions && Object.prototype.hasOwnProperty.call(actions, 'POST');
  const isAllSelected = selected.length > 0 && selected.length === hosts.length;

  return (
    <>
      <PaginatedTable
        contentError={contentError}
        hasContentLoading={isLoading || isDeleteLoading || isAdHocLaunchLoading}
        items={hosts}
        itemCount={hostCount}
        pluralizedItemName={t`Hosts`}
        qsConfig={QS_CONFIG}
        toolbarSearchableKeys={searchableKeys}
        toolbarRelatedSearchableKeys={relatedSearchableKeys}
        headerRow={
          <HeaderRow qsConfig={QS_CONFIG}>
            <HeaderCell sortKey="name">{t`Name`}</HeaderCell>
            <HeaderCell>{t`Actions`}</HeaderCell>
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
                ? [
                    <ToolbarAddButton
                      key="add"
                      linkTo={`/inventories/inventory/${id}/hosts/add`}
                    />,
                  ]
                : []),
              <AdHocCommands
                adHocItems={selected}
                hasListItems={hostCount > 0}
                onLaunchLoading={setIsAdHocLaunchLoading}
              />,
              <ToolbarDeleteButton
                key="delete"
                onDelete={handleDeleteHosts}
                itemsToDelete={selected}
                pluralizedItemName={t`Hosts`}
              />,
            ]}
          />
        )}
        renderRow={(host, index) => (
          <InventoryHostItem
            key={host.id}
            host={host}
            detailUrl={`/inventories/inventory/${id}/hosts/${host.id}/details`}
            editUrl={`/inventories/inventory/${id}/hosts/${host.id}/edit`}
            isSelected={selected.some(row => row.id === host.id)}
            onSelect={() => handleSelect(host)}
            rowIndex={index}
          />
        )}
        emptyStateControls={
          canAdd && (
            <ToolbarAddButton
              key="add"
              linkTo={`/inventories/inventory/${id}/add`}
            />
          )
        }
      />
      {deletionError && (
        <AlertModal
          isOpen={deletionError}
          variant="error"
          title={t`Error!`}
          onClose={clearDeletionError}
        >
          {t`Failed to delete one or more hosts.`}
          <ErrorDetail error={deletionError} />
        </AlertModal>
      )}
    </>
  );
}

export default InventoryHostList;
