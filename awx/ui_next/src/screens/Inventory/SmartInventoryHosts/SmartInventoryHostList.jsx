import React, { useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import DataListToolbar from '../../../components/DataListToolbar';
import PaginatedDataList from '../../../components/PaginatedDataList';
import SmartInventoryHostListItem from './SmartInventoryHostListItem';
import useRequest from '../../../util/useRequest';
import useSelected from '../../../util/useSelected';
import { getQSConfig, parseQueryString } from '../../../util/qs';
import { InventoriesAPI } from '../../../api';
import { Inventory } from '../../../types';
import AdHocCommands from '../../../components/AdHocCommands/AdHocCommands';

const QS_CONFIG = getQSConfig('host', {
  page: 1,
  page_size: 20,
  order_by: 'name',
});

function SmartInventoryHostList({ i18n, inventory }) {
  const location = useLocation();

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

  const { selected, isAllSelected, handleSelect, setSelected } = useSelected(
    hosts
  );

  useEffect(() => {
    fetchHosts();
  }, [fetchHosts]);

  return (
    <>
      <PaginatedDataList
        contentError={contentError}
        hasContentLoading={isLoading}
        items={hosts}
        itemCount={count}
        pluralizedItemName={i18n._(t`Hosts`)}
        qsConfig={QS_CONFIG}
        onRowClick={handleSelect}
        toolbarSearchColumns={[
          {
            name: i18n._(t`Name`),
            key: 'name',
            isDefault: true,
          },
          {
            name: i18n._(t`Created by (username)`),
            key: 'created_by__username',
          },
          {
            name: i18n._(t`Modified by (username)`),
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
            onSelectAll={isSelected =>
              setSelected(isSelected ? [...hosts] : [])
            }
            qsConfig={QS_CONFIG}
            additionalControls={
              inventory?.summary_fields?.user_capabilities?.adhoc
                ? [
                    <AdHocCommands
                      adHocItems={selected}
                      hasListItems={count > 0}
                    />,
                  ]
                : []
            }
          />
        )}
        renderItem={host => (
          <SmartInventoryHostListItem
            key={host.id}
            host={host}
            detailUrl={`/inventories/smart_inventory/${inventory.id}/hosts/${host.id}/details`}
            isSelected={selected.some(row => row.id === host.id)}
            onSelect={() => handleSelect(host)}
          />
        )}
      />
    </>
  );
}

SmartInventoryHostList.propTypes = {
  inventory: Inventory.isRequired,
};

export default withI18n()(SmartInventoryHostList);
