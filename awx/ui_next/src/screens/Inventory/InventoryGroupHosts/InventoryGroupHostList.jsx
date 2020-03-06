import React, { useEffect, useCallback, useState } from 'react';
import { useHistory, useLocation, useParams } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { getQSConfig, parseQueryString } from '@util/qs';
import { GroupsAPI, InventoriesAPI } from '@api';

import AlertModal from '@components/AlertModal';
import DataListToolbar from '@components/DataListToolbar';
import PaginatedDataList from '@components/PaginatedDataList';
import useRequest from '@util/useRequest';
import InventoryGroupHostListItem from './InventoryGroupHostListItem';
import AddHostDropdown from './AddHostDropdown';

const QS_CONFIG = getQSConfig('host', {
  page: 1,
  page_size: 20,
  order_by: 'name',
});

function InventoryGroupHostList({ i18n }) {
  const [selected, setSelected] = useState([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const { id: inventoryId, groupId } = useParams();
  const location = useLocation();
  const history = useHistory();

  const {
    result: { hosts, hostCount, actions },
    error: contentError,
    isLoading,
    request: fetchHosts,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);
      const [response, actionsResponse] = await Promise.all([
        GroupsAPI.readAllHosts(groupId, params),
        InventoriesAPI.readHostsOptions(inventoryId),
      ]);

      return {
        hosts: response.data.results,
        hostCount: response.data.count,
        actions: actionsResponse.data.actions,
      };
    }, [groupId, inventoryId, location.search]),
    {
      hosts: [],
      hostCount: 0,
    }
  );

  useEffect(() => {
    fetchHosts();
  }, [fetchHosts]);

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

  const isAllSelected = selected.length > 0 && selected.length === hosts.length;
  const canAdd =
    actions && Object.prototype.hasOwnProperty.call(actions, 'POST');
  const addFormUrl = `/inventories/inventory/${inventoryId}/groups/${groupId}/nested_hosts/add`;

  return (
    <>
      <PaginatedDataList
        contentError={contentError}
        hasContentLoading={isLoading}
        items={hosts}
        itemCount={hostCount}
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
                ? [
                    <AddHostDropdown
                      onAddExisting={() => setIsModalOpen(true)}
                      onAddNew={() => history.push(addFormUrl)}
                    />,
                  ]
                : []),
              // TODO HOST DISASSOCIATE BUTTON
            ]}
          />
        )}
        renderItem={o => (
          <InventoryGroupHostListItem
            key={o.id}
            host={o}
            detailUrl={`/inventories/inventory/${inventoryId}/hosts/${o.id}/details`}
            editUrl={`/inventories/inventory/${inventoryId}/hosts/${o.id}/edit`}
            isSelected={selected.some(row => row.id === o.id)}
            onSelect={() => handleSelect(o)}
          />
        )}
        emptyStateControls={
          canAdd && (
            <AddHostDropdown
              onAddExisting={() => setIsModalOpen(true)}
              onAddNew={() => history.push(addFormUrl)}
            />
          )
        }
      />

      {/* DISASSOCIATE HOST MODAL PLACEHOLDER */}

      {isModalOpen && (
        <AlertModal
          isOpen={isModalOpen}
          variant="info"
          title={i18n._(t`Select Hosts`)}
          onClose={() => setIsModalOpen(false)}
        >
          {/* ADD/ASSOCIATE HOST MODAL PLACEHOLDER */}
          {i18n._(t`Host Select Modal`)}
        </AlertModal>
      )}
    </>
  );
}

export default withI18n()(InventoryGroupHostList);
