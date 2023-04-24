import React, { useCallback, useEffect } from 'react';
import { t } from '@lingui/macro';
import { CardBody } from 'components/Card';
import PaginatedTable, {
  getSearchableKeys,
  HeaderCell,
  HeaderRow,
} from 'components/PaginatedTable';
import { getQSConfig, parseQueryString } from 'util/qs';
import { useLocation, useParams } from 'react-router-dom';
import useRequest, { useDeleteItems } from 'hooks/useRequest';
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

function InstancePeerList() {
  const location = useLocation();
  const { id } = useParams();
  const [isModalOpen, setIsModalOpen] = useState(false);
  
  const isSysAdmin = roles.some((role) => role.name === 'System Administrator');
  
  const fetchInstancesToAssociate = useCallback(
    (params) =>
      InstancesAPI.read(params),
    [instanceId]
  );
  
  const {
    isLoading,
    error: contentError,
    request: fetchPeers,
    result: { peers, count, relatedSearchableKeys, searchableKeys },
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);
      const [
        {
          data: { results, count: itemNumber },
        },
        actions,
      ] = await Promise.all([
        InstancesAPI.readPeers(id, params),
        InstancesAPI.readOptions(),
      ]);
      return {
        peers: results,
        count: itemNumber,
        relatedSearchableKeys: (actions?.data?.related_search_fields || []).map(
          (val) => val.slice(0, -8)
        ),
        searchableKeys: getSearchableKeys(actions.data.actions?.GET),
      };
    }, [id, location]),
    {
      peers: [],
      count: 0,
      relatedSearchableKeys: [],
      searchableKeys: [],
    }
  );

  useEffect(() => {
    fetchPeers();
  }, [fetchPeers]);

  const { expanded, isAllExpanded, handleExpand, expandAll } =
    useExpanded(peers);
  
  const { selected, isAllSelected, handleSelect, clearSelected, selectAll } =
    useSelected(peers);

  const { error, dismissError } = useDismissableError(
    associateError || disassociateError
  );

  const { 
    request: handlePeerAssociate, 
    error: associateError 
  } = useRequest(
    useCallback(
      async (instancesPeerToAssociate) => {
        await Promise.all(
          instancesPeerToAssociate
            .filter((i) => i.node_type !== 'control')
            .map((target) =>
              PeersAPI.addPeer(id, target.id)
            )
        );
        fetchPeers();
      },
      [id, fetchPeers]
    )
  );

  const {
    isLoading: isDisassociateLoading,
    deleteItems: deletePeers,
    deletionError: disassociateError,
    clearDeletionError,
  } = useDeleteItems(
    useCallback(
      () => 
        Promise.all(
          selected.map((target) =>
              PeersAPI.deletePeer(id, target.id)
          )
        ),
      [id, selected]
    ),
    {
      qsConfig: QS_CONFIG,
      allItemsSelected: isAllSelected,
      fetchItems: fetchPeers,
    }
  );
  
  const canAdd = isSysAdmin;
  

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
                      onClick={() => setShowAddModal(true)}
                    />,
                  ]
                : []),
              <DisassociateButton
                verifyCannotDisassociate={false}
                key="disassociate"
                onDisassociate={handlePeersDiassociate}
                itemsToDisassociate={selected}
                modalTitle={t`Disassociate instance from peers?`}
                isProtectedInstanceGroup={instanceGroup.name === 'controlplane'}
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
         // optionsRequest={readInstancesOptions}
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
