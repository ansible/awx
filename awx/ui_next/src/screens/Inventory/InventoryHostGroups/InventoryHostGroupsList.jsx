import React, { useState, useEffect, useCallback } from 'react';
import { withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { getQSConfig, parseQueryString } from '@util/qs';
import useRequest from '@util/useRequest';
import { HostsAPI } from '@api';
import DataListToolbar from '@components/DataListToolbar';
import PaginatedDataList from '@components/PaginatedDataList';
import InventoryHostGroupItem from './InventoryHostGroupItem';

const QS_CONFIG = getQSConfig('group', {
  page: 1,
  page_size: 20,
  order_by: 'name',
});

function InventoryHostGroupsList({ i18n, location, match }) {
  const [selected, setSelected] = useState([]);

  const { hostId } = match.params;

  const {
    result: { groups, itemCount },
    error: contentError,
    isLoading,
    request: fetchGroups,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);

      const {
        data: { count, results },
      } = await HostsAPI.readGroups(hostId, params);

      return {
        itemCount: count,
        groups: results,
      };
    }, [hostId, location]), // eslint-disable-line react-hooks/exhaustive-deps
    {
      groups: [],
      itemCount: 0,
    }
  );

  useEffect(() => {
    fetchGroups();
  }, [fetchGroups]);

  const handleSelectAll = isSelected => {
    setSelected(isSelected ? [...groups] : []);
  };

  const handleSelect = row => {
    if (selected.some(s => s.id === row.id)) {
      setSelected(selected.filter(s => s.id !== row.id));
    } else {
      setSelected(selected.concat(row));
    }
  };

  const isAllSelected =
    selected.length > 0 && selected.length === groups.length;

  return (
    <>
      <PaginatedDataList
        contentError={contentError}
        hasContentLoading={isLoading}
        items={groups}
        itemCount={itemCount}
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
        renderItem={item => (
          <InventoryHostGroupItem
            key={item.id}
            group={item}
            inventoryId={item.summary_fields.inventory.id}
            isSelected={selected.some(row => row.id === item.id)}
            onSelect={() => handleSelect(item)}
          />
        )}
        renderToolbar={props => (
          <DataListToolbar
            {...props}
            showSelectAll
            isAllSelected={isAllSelected}
            onSelectAll={handleSelectAll}
            qsConfig={QS_CONFIG}
          />
        )}
      />
    </>
  );
}
export default withI18n()(withRouter(InventoryHostGroupsList));
