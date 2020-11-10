import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useLocation } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { getQSConfig, parseQueryString } from '../../../util/qs';
import { InventoriesAPI, HostsAPI } from '../../../api';
import useRequest, { useDeleteItems } from '../../../util/useRequest';
import AlertModal from '../../../components/AlertModal';
import DataListToolbar from '../../../components/DataListToolbar';
import ErrorDetail from '../../../components/ErrorDetail';
import PaginatedDataList, {
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

function InventoryHostList({ i18n }) {
  const [selected, setSelected] = useState([]);
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
    useCallback(async () => {
      await Promise.all(selected.map(host => HostsAPI.destroy(host.id)));
    }, [selected]),
    { qsConfig: QS_CONFIG, fetchItems: fetchData }
  );

  const canAdd =
    actions && Object.prototype.hasOwnProperty.call(actions, 'POST');
  const isAllSelected = selected.length > 0 && selected.length === hosts.length;

  return (
    <>
      <PaginatedDataList
        contentError={contentError}
        hasContentLoading={isLoading || isDeleteLoading}
        items={hosts}
        itemCount={hostCount}
        pluralizedItemName={i18n._(t`Hosts`)}
        qsConfig={QS_CONFIG}
        toolbarColumns={[
          {
            name: i18n._(t`Name`),
            key: 'name',
            isSortable: true,
            isSearchable: true,
          },
          {
            name: i18n._(t`Modified`),
            key: 'modified',
            isSortable: true,
            isNumeric: true,
          },
          {
            name: i18n._(t`Created`),
            key: 'created',
            isSortable: true,
            isNumeric: true,
          },
        ]}
        toolbarSearchableKeys={searchableKeys}
        toolbarRelatedSearchableKeys={relatedSearchableKeys}
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
              />,
              <ToolbarDeleteButton
                key="delete"
                onDelete={deleteHosts}
                itemsToDelete={selected}
                pluralizedItemName={i18n._(t`Hosts`)}
              />,
            ]}
          />
        )}
        renderItem={o => (
          <InventoryHostItem
            key={o.id}
            host={o}
            detailUrl={`/inventories/inventory/${id}/hosts/${o.id}/details`}
            editUrl={`/inventories/inventory/${id}/hosts/${o.id}/edit`}
            isSelected={selected.some(row => row.id === o.id)}
            onSelect={() => handleSelect(o)}
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
          title={i18n._(t`Error!`)}
          onClose={clearDeletionError}
        >
          {i18n._(t`Failed to delete one or more hosts.`)}
          <ErrorDetail error={deletionError} />
        </AlertModal>
      )}
    </>
  );
}

export default withI18n()(InventoryHostList);
