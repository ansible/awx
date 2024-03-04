import React, { useCallback, useEffect } from 'react';
import { t } from '@lingui/macro';
import { CardBody } from 'components/Card';
import PaginatedTable, {
  getSearchableKeys,
  HeaderCell,
  HeaderRow,
  // ToolbarAddButton,
} from 'components/PaginatedTable';
import useToast from 'hooks/useToast';
import { getQSConfig } from 'util/qs';
import { useParams } from 'react-router-dom';
import useRequest from 'hooks/useRequest';
import DataListToolbar from 'components/DataListToolbar';
import { InstancesAPI, ReceptorAPI } from 'api';
import useSelected from 'hooks/useSelected';
import InstanceListenerAddressListItem from './InstanceListenerAddressListItem';

const QS_CONFIG = getQSConfig('peer', {
  page: 1,
  page_size: 20,
  order_by: 'pk',
});

function InstanceListenerAddressList({ setBreadcrumb }) {
  const { id } = useParams();
  const { Toast, toastProps } = useToast();
  const {
    isLoading,
    error: contentError,
    request: fetchListenerAddresses,
    result: {
      instance,
      listenerAddresses,
      count,
      relatedSearchableKeys,
      searchableKeys,
    },
  } = useRequest(
    useCallback(async () => {
      const [
        { data: detail },
        {
          data: { results },
        },
        actions,
      ] = await Promise.all([
        InstancesAPI.readDetail(id),
        ReceptorAPI.read(),
        InstancesAPI.readOptions(),
      ]);

      const listenerAddress_list = [];

      for (let q = 0; q < results.length; q++) {
        const receptor = results[q];
        if (receptor.managed === true) continue;
        if (id.toString() === receptor.instance.toString()) {
          receptor.name = detail.hostname;
          listenerAddress_list.push(receptor);
        }
      }

      return {
        instance: detail,
        listenerAddresses: listenerAddress_list,
        count: listenerAddress_list.length,
        relatedSearchableKeys: (actions?.data?.related_search_fields || []).map(
          (val) => val.slice(0, -8)
        ),
        searchableKeys: getSearchableKeys(actions.data.actions?.GET),
      };
    }, [id]),
    {
      instance: {},
      listenerAddresses: [],
      count: 0,
      relatedSearchableKeys: [],
      searchableKeys: [],
    }
  );

  useEffect(() => {
    fetchListenerAddresses();
  }, [fetchListenerAddresses]);

  useEffect(() => {
    if (instance) {
      setBreadcrumb(instance);
    }
  }, [instance, setBreadcrumb]);

  const { selected, isAllSelected, handleSelect, clearSelected, selectAll } =
    useSelected(listenerAddresses);

  return (
    <CardBody>
      <PaginatedTable
        contentError={contentError}
        hasContentLoading={isLoading}
        items={listenerAddresses}
        itemCount={count}
        pluralizedItemName={t`Listener Addresses`}
        qsConfig={QS_CONFIG}
        onRowClick={handleSelect}
        clearSelected={clearSelected}
        toolbarSearchableKeys={searchableKeys}
        toolbarRelatedSearchableKeys={relatedSearchableKeys}
        toolbarSearchColumns={[
          {
            name: t`Name`,
            key: 'hostname__icontains',
            isDefault: true,
          },
        ]}
        toolbarSortColumns={[
          {
            name: t`Name`,
            key: 'hostname',
          },
        ]}
        headerRow={
          <HeaderRow qsConfig={QS_CONFIG}>
            <HeaderCell sortKey="address">{t`Address`}</HeaderCell>
            <HeaderCell sortKey="port">{t`Port`}</HeaderCell>
            <HeaderCell sortKey="protocol">{t`Protocol`}</HeaderCell>
            <HeaderCell sortKey="canonical">{t`Canonical`}</HeaderCell>
          </HeaderRow>
        }
        renderToolbar={(props) => (
          <DataListToolbar
            {...props}
            isAllSelected={isAllSelected}
            onSelectAll={selectAll}
            qsConfig={QS_CONFIG}
            additionalControls={[]}
          />
        )}
        renderRow={(listenerAddress, index) => (
          <InstanceListenerAddressListItem
            isSelected={selected.some((row) => row.id === listenerAddress.id)}
            onSelect={() => handleSelect(listenerAddress)}
            key={listenerAddress.id}
            peerListenerAddress={listenerAddress}
            rowIndex={index}
          />
        )}
      />
      <Toast {...toastProps} />
    </CardBody>
  );
}

export default InstanceListenerAddressList;
