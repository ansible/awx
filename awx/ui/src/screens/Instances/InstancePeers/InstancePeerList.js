import React, { useCallback, useEffect, useState } from 'react';
import { t } from '@lingui/macro';
import { CardBody } from 'components/Card';
import PaginatedTable, {
  getSearchableKeys,
  HeaderCell,
  HeaderRow,
  ToolbarAddButton,
} from 'components/PaginatedTable';
import DisassociateButton from 'components/DisassociateButton';
import AssociateModal from 'components/AssociateModal';
import ErrorDetail from 'components/ErrorDetail';
import AlertModal from 'components/AlertModal';
import { getQSConfig, parseQueryString, mergeParams } from 'util/qs';
import { useLocation, useParams } from 'react-router-dom';
import useRequest, { useDeleteItems, useDismissableError } from 'hooks/useRequest';
import DataListToolbar from 'components/DataListToolbar';
import { InstancesAPI, PeersAPI } from 'api';
import useExpanded from 'hooks/useExpanded';
import useSelected from 'hooks/useSelected';
import InstancePeerListItem from './InstancePeerListItem';

const QS_CONFIG = getQSConfig('peer', {
  page: 1,
  page_size: 20,
  order_by: 'hostname',
});

function InstancePeerList({ setBreadcrumb }) {
  const location = useLocation();
  const { id } = useParams();
  const [isModalOpen, setIsModalOpen] = useState(false);

  // const isSysAdmin = roles.some((role) => role.name === 'System Administrator');

  const readInstancesOptions = useCallback(
    () => InstancesAPI.readOptions(id),
    [id]
  );

  const {
    isLoading,
    error: contentError,
    request: fetchPeers,
    result: { instance, peers, count, relatedSearchableKeys, searchableKeys },
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);
      const [
        { data: instance_detail },
        {
          data: { results, count: itemNumber },
        },
        actions,
      ] = await Promise.all([
        InstancesAPI.readDetail(id),
        InstancesAPI.readPeers(id, params),
        InstancesAPI.readOptions(),
      ]);
      return {
        instance: instance_detail,
        peers: results,
        count: itemNumber,
        relatedSearchableKeys: (actions?.data?.related_search_fields || []).map(
          (val) => val.slice(0, -8)
        ),
        searchableKeys: getSearchableKeys(actions.data.actions?.GET),
      };
    }, [id, location]),
    {
      instance: {},
      peers: [],
      count: 0,
      relatedSearchableKeys: [],
      searchableKeys: [],
    }
  );

  useEffect(() => {
    fetchPeers();
  }, [fetchPeers]);

  useEffect(() => {
    if (instance) {
      setBreadcrumb(instance);
    }
  }, [instance, setBreadcrumb]);

  const { expanded, isAllExpanded, handleExpand, expandAll } =
    useExpanded(peers);
  const { selected, isAllSelected, handleSelect, clearSelected, selectAll } =
    useSelected(peers);

  const { error, dismissError } = useDismissableError(
    associateError || disassociateError
  );

  const fetchInstancesToAssociate = useCallback(
    (params) =>
      InstancesAPI.read(
        mergeParams(params, {
          ...{ not__id: id },
          ...{ not__node_type: ['control', 'hybrid'] },
          ...{ not__hostname: instance.peers }
        })
      ),
    [id, instance]
  );

  const {
    request: handlePeerAssociate,
    error: associateError
  } = useRequest(
    useCallback(
      async (instancesPeerToAssociate) => {
        await Promise.all(
          instancesPeerToAssociate
            .map((target) =>
              PeersAPI.createPeer(instance.hostname, target.hostname)
            )
        );
        fetchPeers();
      },
      [id, instance, fetchPeers]
    )
  );

  const {
    isLoading: isDisassociateLoading,
    deleteItems: deletePeers,
    deletionError: disassociateError,
  } = useDeleteItems(
    useCallback(
      async () => {
        await Promise.all(
          selected.map((target) =>
            PeersAPI.destroyPeer(instance.hostname, target.hostname)
          )
        );
      },
      [id, selected]
    ),
    {
      qsConfig: QS_CONFIG,
      allItemsSelected: isAllSelected,
      fetchItems: fetchPeers,
    }
  );

  const canAdd = true;

  const handlePeersDiassociate = async () => {
    await deletePeers();
    clearSelected();
  };

  return (
    <CardBody>
      <PaginatedTable
        contentError={contentError}
        hasContentLoading={isLoading || isDisassociateLoading}
        items={peers}
        itemCount={count}
        pluralizedItemName={t`Peers`}
        qsConfig={QS_CONFIG}
        onRowClick={handleSelect}
        toolbarSearchableKeys={searchableKeys}
        toolbarRelatedSearchableKeys={relatedSearchableKeys}
        clearSelected={clearSelected}
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
          <HeaderRow qsConfig={QS_CONFIG} isExpandable>
            <HeaderCell
              tooltip={t`Cannot run health check on hop nodes.`}
              sortKey="hostname"
            >{t`Name`}</HeaderCell>
            <HeaderCell sortKey="errors">{t`Status`}</HeaderCell>
            <HeaderCell sortKey="node_type">{t`Node Type`}</HeaderCell>
          </HeaderRow>
        }
        renderToolbar={(props) => (
          <DataListToolbar
            {...props}
            isAllSelected={isAllSelected}
            onSelectAll={selectAll}
            isAllExpanded={isAllExpanded}
            onExpandAll={expandAll}
            qsConfig={QS_CONFIG}
            additionalControls={[
              ...(canAdd
                ? [
                    <ToolbarAddButton
                      ouiaId="add-instance-peers-button"
                      key="add"
                      onClick={() => setIsModalOpen(true)}
                    />,
                  ]
                : []),
              <DisassociateButton
                verifyCannotDisassociate={false}
                key="disassociate"
                onDisassociate={handlePeersDiassociate}
                itemsToDisassociate={selected}
                modalTitle={t`Disassociate instance from peers?`}
              />,
            ]}
          />
        )}
        renderRow={(peer, index) => (
          <InstancePeerListItem
            isSelected={selected.some((row) => row.id === peer.id)}
            onSelect={() => handleSelect(peer)}
            isExpanded={expanded.some((row) => row.id === peer.id)}
            onExpand={() => handleExpand(peer)}
            key={peer.id}
            peerInstance={peer}
            rowIndex={index}
          />
        )}
      />
      {isModalOpen && (
        <AssociateModal
          header={t`Instances`}
          fetchRequest={fetchInstancesToAssociate}
          isModalOpen={isModalOpen}
          onAssociate={handlePeerAssociate}
          onClose={() => setIsModalOpen(false)}
          title={t`Select Instances`}
          optionsRequest={readInstancesOptions}
          displayKey="hostname"
          columns={[
            { key: 'hostname', name: t`Name` },
            { key: 'node_type', name: t`Node Type` },
          ]}
        />
      )}
      {error && (
        <AlertModal
          isOpen={error}
          onClose={dismissError}
          title={t`Error!`}
          variant="error"
        >
          {associateError && t`Failed to associate peer.`}
          {disassociateError &&
            t`Failed to remove one or more peers.`}
          <ErrorDetail error={error} />
        </AlertModal>
      )}
    </CardBody>
  );
}

export default InstancePeerList;
