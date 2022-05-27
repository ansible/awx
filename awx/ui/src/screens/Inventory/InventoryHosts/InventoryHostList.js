import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useLocation } from 'react-router-dom';
import { t } from '@lingui/macro';
import { getQSConfig, parseQueryString } from 'util/qs';
import { InventoriesAPI, HostsAPI } from 'api';
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
import useSelected from 'hooks/useSelected';
import AdHocCommands from 'components/AdHocCommands/AdHocCommands';
import InventoryHostItem from './InventoryHostItem';

const QS_CONFIG = getQSConfig('host', {
  page: 1,
  page_size: 20,
  order_by: 'name',
});

function InventoryHostList() {
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
      moduleOptions,
      isAdHocDisabled,
    },
    error: contentError,
    isLoading,
    request: fetchData,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, search);
      const [response, hostOptions, adHocOptions] = await Promise.all([
        InventoriesAPI.readHosts(id, params),
        InventoriesAPI.readHostsOptions(id),
        InventoriesAPI.readAdHocOptions(id),
      ]);

      return {
        moduleOptions: adHocOptions.data.actions.GET.module_name.choices,
        isAdHocDisabled: !adHocOptions.data.actions.POST,
        hosts: response.data.results,
        hostCount: response.data.count,
        actions: hostOptions.data.actions,
        relatedSearchableKeys: (
          hostOptions?.data?.related_search_fields || []
        ).map((val) => (val.endsWith('search') ? val.slice(0, -8) : val)),
        searchableKeys: getSearchableKeys(hostOptions.data.actions?.GET),
      };
    }, [id, search]),
    {
      hosts: [],
      hostCount: 0,
      actions: {},
      relatedSearchableKeys: [],
      searchableKeys: [],
      moduleOptions: [],
      isAdHocDisabled: true,
    }
  );

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const { selected, isAllSelected, handleSelect, selectAll, clearSelected } =
    useSelected(hosts);

  const {
    isLoading: isDeleteLoading,
    deleteItems: deleteHosts,
    deletionError,
    clearDeletionError,
  } = useDeleteItems(
    useCallback(
      () => Promise.all(selected.map((host) => HostsAPI.destroy(host.id))),
      [selected]
    ),
    { qsConfig: QS_CONFIG, fetchItems: fetchData }
  );

  const handleDeleteHosts = async () => {
    await deleteHosts();
    clearSelected();
  };

  const canAdd =
    actions && Object.prototype.hasOwnProperty.call(actions, 'POST');

  return (
    <>
      <PaginatedTable
        contentError={contentError}
        hasContentLoading={isLoading || isDeleteLoading || isAdHocLaunchLoading}
        items={hosts}
        itemCount={hostCount}
        pluralizedItemName={t`Hosts`}
        qsConfig={QS_CONFIG}
        clearSelected={clearSelected}
        toolbarSearchableKeys={searchableKeys}
        toolbarRelatedSearchableKeys={relatedSearchableKeys}
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
        headerRow={
          <HeaderRow qsConfig={QS_CONFIG}>
            <HeaderCell sortKey="name">{t`Name`}</HeaderCell>
            <HeaderCell sortKey="description">{t`Description`}</HeaderCell>
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
                ? [
                    <ToolbarAddButton
                      key="add"
                      linkTo={`/inventories/inventory/${id}/hosts/add`}
                    />,
                  ]
                : []),
              ...(!isAdHocDisabled
                ? [
                    <AdHocCommands
                      moduleOptions={moduleOptions}
                      adHocItems={selected}
                      hasListItems={hostCount > 0}
                      onLaunchLoading={setIsAdHocLaunchLoading}
                    />,
                  ]
                : []),
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
            isSelected={selected.some((row) => row.id === host.id)}
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
