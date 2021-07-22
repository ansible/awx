import React, { useEffect, useCallback, useState } from 'react';
import { useLocation } from 'react-router-dom';

import { t } from '@lingui/macro';
import DataListToolbar from 'components/DataListToolbar';
import PaginatedTable, {
  HeaderRow,
  HeaderCell,
} from 'components/PaginatedTable';
import useRequest from 'hooks/useRequest';
import useSelected from 'hooks/useSelected';
import { getQSConfig, parseQueryString } from 'util/qs';
import { InventoriesAPI } from 'api';
import { Inventory } from 'types';
import AdHocCommands from 'components/AdHocCommands/AdHocCommands';
import SmartInventoryHostListItem from './SmartInventoryHostListItem';

const QS_CONFIG = getQSConfig('host', {
  page: 1,
  page_size: 20,
  order_by: 'name',
});

function SmartInventoryHostList({ inventory }) {
  const location = useLocation();
  const [isAdHocLaunchLoading, setIsAdHocLaunchLoading] = useState(false);
  const {
    result: { hosts, count },
    error: contentError,
    isLoading,
    request: fetchHosts,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);
      const {
        data: { results, count: hostCount },
      } = await InventoriesAPI.readHosts(inventory.id, params);

      return {
        hosts: results,
        count: hostCount,
      };
    }, [location.search, inventory.id]),
    {
      hosts: [],
      count: 0,
    }
  );

  const { selected, isAllSelected, handleSelect, clearSelected, selectAll } =
    useSelected(hosts);

  useEffect(() => {
    fetchHosts();
  }, [fetchHosts]);

  return (
    <>
      <PaginatedTable
        contentError={contentError}
        hasContentLoading={isLoading || isAdHocLaunchLoading}
        items={hosts}
        itemCount={count}
        pluralizedItemName={t`Hosts`}
        qsConfig={QS_CONFIG}
        clearSelected={clearSelected}
        toolbarSearchColumns={[
          {
            name: t`Name`,
            key: 'name',
            isDefault: true,
          },
          {
            name: t`Created by (username)`,
            key: 'created_by__username',
          },
          {
            name: t`Modified by (username)`,
            key: 'modified_by__username',
          },
        ]}
        renderToolbar={(props) => (
          <DataListToolbar
            {...props}
            isAllSelected={isAllSelected}
            onSelectAll={selectAll}
            qsConfig={QS_CONFIG}
            additionalControls={
              inventory?.summary_fields?.user_capabilities?.adhoc
                ? [
                    <AdHocCommands
                      adHocItems={selected}
                      hasListItems={count > 0}
                      onLaunchLoading={setIsAdHocLaunchLoading}
                    />,
                  ]
                : []
            }
          />
        )}
        headerRow={
          <HeaderRow qsConfig={QS_CONFIG}>
            <HeaderCell sortKey="name">{t`Name`}</HeaderCell>
            <HeaderCell>{t`Recent jobs`}</HeaderCell>
            <HeaderCell>{t`Inventory`}</HeaderCell>
          </HeaderRow>
        }
        renderRow={(host, index) => (
          <SmartInventoryHostListItem
            key={host.id}
            host={host}
            detailUrl={`/inventories/smart_inventory/${inventory.id}/hosts/${host.id}/details`}
            isSelected={selected.some((row) => row.id === host.id)}
            onSelect={() => handleSelect(host)}
            rowIndex={index}
          />
        )}
      />
    </>
  );
}

SmartInventoryHostList.propTypes = {
  inventory: Inventory.isRequired,
};

export default SmartInventoryHostList;
