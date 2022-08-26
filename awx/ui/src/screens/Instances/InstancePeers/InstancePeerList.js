import React, { useCallback, useEffect } from 'react';
import { t } from '@lingui/macro';
import { CardBody } from 'components/Card';
import PaginatedTable, {
  getSearchableKeys,
  HeaderCell,
  HeaderRow,
} from 'components/PaginatedTable';
import useRequest, { useDismissableError } from 'hooks/useRequest';
import { getQSConfig } from 'util/qs';
import { useParams } from 'react-router-dom';
import DataListToolbar from 'components/DataListToolbar';
import { InstancesAPI } from 'api';
import useExpanded from 'hooks/useExpanded';
import ErrorDetail from 'components/ErrorDetail';
import useSelected from 'hooks/useSelected';
import HealthCheckButton from 'components/HealthCheckButton';
import AlertModal from 'components/AlertModal';
import InstancePeerListItem from './InstancePeerListItem';

const QS_CONFIG = getQSConfig('peer', {
  page: 1,
  page_size: 20,
  order_by: 'hostname',
});

function InstancePeerList() {
  const { id } = useParams();
  const {
    isLoading,
    error: contentError,
    request: fetchPeers,
    result: { peers, count, relatedSearchableKeys, searchableKeys },
  } = useRequest(
    useCallback(async () => {
      const [
        {
          data: { results, count: itemNumber },
        },
        actions,
      ] = await Promise.all([
        InstancesAPI.readPeers(id),
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
    }, [id]),
    {
      peers: [],
      count: 0,
      relatedSearchableKeys: [],
      searchableKeys: [],
    }
  );

  useEffect(() => fetchPeers(), [fetchPeers, id]);

  const { selected, isAllSelected, handleSelect, clearSelected, selectAll } =
    useSelected(peers.filter((i) => i.node_type !== 'hop'));

  const {
    error: healthCheckError,
    request: fetchHealthCheck,
    isLoading: isHealthCheckLoading,
  } = useRequest(
    useCallback(async () => {
      await Promise.all(
        selected
          .filter(({ node_type }) => node_type !== 'hop')
          .map(({ instanceId }) => InstancesAPI.healthCheck(instanceId))
      );
      fetchPeers();
    }, [selected, fetchPeers])
  );
  const handleHealthCheck = async () => {
    await fetchHealthCheck();
    clearSelected();
  };

  const { error, dismissError } = useDismissableError(healthCheckError);

  const { expanded, isAllExpanded, handleExpand, expandAll } =
    useExpanded(peers);

  return (
    <CardBody>
      <PaginatedTable
        contentError={contentError}
        hasContentLoading={isLoading || isHealthCheckLoading}
        items={peers}
        itemCount={count}
        pluralizedItemName={t`Peers`}
        qsConfig={QS_CONFIG}
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
        renderToolbar={(props) => (
          <DataListToolbar
            {...props}
            isAllSelected={isAllSelected}
            onSelectAll={selectAll}
            isAllExpanded={isAllExpanded}
            onExpandAll={expandAll}
            qsConfig={QS_CONFIG}
            additionalControls={[
              <HealthCheckButton
                onClick={handleHealthCheck}
                selectedItems={selected}
              />,
            ]}
          />
        )}
        headerRow={
          <HeaderRow qsConfig={QS_CONFIG}>
            <HeaderCell sortKey="hostname">{t`Name`}</HeaderCell>
          </HeaderRow>
        }
        renderRow={(peer, index) => (
          <InstancePeerListItem
            onSelect={() => handleSelect(peer)}
            isSelected={selected.some((row) => row.id === peer.id)}
            isExpanded={expanded.some((row) => row.id === peer.id)}
            onExpand={() => handleExpand(peer)}
            key={peer.id}
            peerInstance={peer}
            rowIndex={index}
            fetchInstance={fetchPeers}
          />
        )}
      />
      {error && (
        <AlertModal
          isOpen={error}
          onClose={dismissError}
          title={t`Error!`}
          variant="error"
        >
          {t`Failed to run a health check on one or more peers.`}
          <ErrorDetail error={error} />
        </AlertModal>
      )}
    </CardBody>
  );
}

export default InstancePeerList;
