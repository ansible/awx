import React, { useEffect, useState } from 'react';
import { withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { getQSConfig, parseQueryString } from '@util/qs';
import { InventoriesAPI, HostsAPI } from '@api';

import AlertModal from '@components/AlertModal';
import DataListToolbar from '@components/DataListToolbar';
import ErrorDetail from '@components/ErrorDetail';
import PaginatedDataList, {
  ToolbarAddButton,
  ToolbarDeleteButton,
} from '@components/PaginatedDataList';
import InventoryHostItem from './InventoryHostItem';

const QS_CONFIG = getQSConfig('host', {
  page: 1,
  page_size: 20,
  order_by: 'name',
});

function InventoryHostList({ i18n, location, match }) {
  const [actions, setActions] = useState(null);
  const [contentError, setContentError] = useState(null);
  const [deletionError, setDeletionError] = useState(null);
  const [hostCount, setHostCount] = useState(0);
  const [hosts, setHosts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selected, setSelected] = useState([]);

  const fetchHosts = (id, queryString) => {
    const params = parseQueryString(QS_CONFIG, queryString);
    return InventoriesAPI.readHosts(id, params);
  };

  useEffect(() => {
    async function fetchData() {
      try {
        const [
          {
            data: { count, results },
          },
          {
            data: { actions: optionActions },
          },
        ] = await Promise.all([
          fetchHosts(match.params.id, location.search),
          InventoriesAPI.readOptions(),
        ]);

        setHosts(results);
        setHostCount(count);
        setActions(optionActions);
      } catch (error) {
        setContentError(error);
      } finally {
        setIsLoading(false);
      }
    }

    fetchData();
  }, [match.params.id, location]);

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

  const handleDelete = async () => {
    setIsLoading(true);

    try {
      await Promise.all(selected.map(host => HostsAPI.destroy(host.id)));
    } catch (error) {
      setDeletionError(error);
    } finally {
      setSelected([]);
      try {
        const {
          data: { count, results },
        } = await fetchHosts(match.params.id, location.search);

        setHosts(results);
        setHostCount(count);
      } catch (error) {
        setContentError(error);
      } finally {
        setIsLoading(false);
      }
    }
  };

  const canAdd =
    actions && Object.prototype.hasOwnProperty.call(actions, 'POST');
  const isAllSelected = selected.length > 0 && selected.length === hosts.length;

  return (
    <>
      <PaginatedDataList
        contentError={contentError}
        hasContentLoading={isLoading}
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
                      linkTo={`/inventories/inventory/${match.params.id}/hosts/add`}
                    />,
                  ]
                : []),
              <ToolbarDeleteButton
                key="delete"
                onDelete={handleDelete}
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
            detailUrl={`/inventories/inventory/${match.params.id}/hosts/${o.id}/details`}
            editUrl={`/inventories/inventory/${match.params.id}/hosts/${o.id}/edit`}
            isSelected={selected.some(row => row.id === o.id)}
            onSelect={() => handleSelect(o)}
          />
        )}
        emptyStateControls={
          canAdd && (
            <ToolbarAddButton
              key="add"
              linkTo={`/inventories/inventory/${match.params.id}/add`}
            />
          )
        }
      />
      {deletionError && (
        <AlertModal
          isOpen={deletionError}
          variant="error"
          title={i18n._(t`Error!`)}
          onClose={() => setDeletionError(null)}
        >
          {i18n._(t`Failed to delete one or more hosts.`)}
          <ErrorDetail error={deletionError} />
        </AlertModal>
      )}
    </>
  );
}

export default withI18n()(withRouter(InventoryHostList));
