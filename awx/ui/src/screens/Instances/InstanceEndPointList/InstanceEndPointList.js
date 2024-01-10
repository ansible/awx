import React, { useCallback, useEffect, useState } from 'react';
import { t } from '@lingui/macro';
import { CardBody } from 'components/Card';
import PaginatedTable, {
  getSearchableKeys,
  HeaderCell,
  HeaderRow,
  // ToolbarAddButton,
} from 'components/PaginatedTable';
import AddEndpointModal from 'components/AddEndpointModal';
import useToast from 'hooks/useToast';
import { getQSConfig } from 'util/qs';
import { useParams } from 'react-router-dom';
import useRequest from 'hooks/useRequest';
import DataListToolbar from 'components/DataListToolbar';
import { InstancesAPI, ReceptorAPI } from 'api';
import useExpanded from 'hooks/useExpanded';
import useSelected from 'hooks/useSelected';
import InstanceEndPointListItem from './InstanceEndPointListItem';

const QS_CONFIG = getQSConfig('peer', {
  page: 1,
  page_size: 20,
  order_by: 'pk',
});

function InstanceEndPointList({ setBreadcrumb }) {
  const { id } = useParams();
  const [isAddEndpointModalOpen, setisAddEndpointModalOpen] = useState(false);
  const { Toast, toastProps } = useToast();
  const {
    isLoading,
    error: contentError,
    request: fetchEndpoints,
    result: { instance, endpoints, count, relatedSearchableKeys, searchableKeys },
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

      const endpoint_list = []

      for(let q = 0; q < results.length; q++) {
        const receptor = results[q];
        if(receptor.managed === true) continue;
        if(id.toString() === receptor.instance.toString()) {
          receptor.name = detail.hostname;
          endpoint_list.push(receptor);
          console.log(receptor)
        }
      }

      return {
        instance: detail,
        endpoints: endpoint_list,
        count: endpoint_list.length,
        relatedSearchableKeys: (actions?.data?.related_search_fields || []).map(
          (val) => val.slice(0, -8)
        ),
        searchableKeys: getSearchableKeys(actions.data.actions?.GET),
      };
    }, [id]),
    {
      instance: {},
      endpoints: [],
      count: 0,
      relatedSearchableKeys: [],
      searchableKeys: [],
    }
  );

  useEffect(() => {
    fetchEndpoints();
  }, [fetchEndpoints]);

  useEffect(() => {
    if (instance) {
      setBreadcrumb(instance);
    }
  }, [instance, setBreadcrumb]);

  const { expanded, isAllExpanded, handleExpand, expandAll } =
    useExpanded(endpoints);
  const { selected, isAllSelected, handleSelect, clearSelected, selectAll } =
    useSelected(endpoints);

  // const handleEndpointDelete = async () => {
  //   // console.log(selected)
  //   // InstancesAPI.updateReceptorAddresses(instance.id, values);
  // }

  // const isHopNode = instance.node_type === 'hop';
  // const isExecutionNode = instance.node_type === 'execution';

  return (
    <CardBody>
      <PaginatedTable
        contentError={contentError}
        hasContentLoading={
          isLoading
        }
        items={endpoints}
        itemCount={count}
        pluralizedItemName={t`Endpoints`}
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
          <HeaderRow qsConfig={QS_CONFIG} isExpandable>
            <HeaderCell sortKey="address">{t`Address`}</HeaderCell>
            <HeaderCell sortKey="port">{t`Port`}</HeaderCell>
            <HeaderCell sortKey="canonical">{t`Canonical`}</HeaderCell>
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
              // (isExecutionNode || isHopNode) && (
              //   <ToolbarAddButton
              //     ouiaId="add-endpoint-button"
              //     key="add-endpoint"
              //     defaultLabel={t`Add`}
              //     onClick={() => setisAddEndpointModalOpen(true)}
              //   />
              // ),
              // (isExecutionNode || isHopNode) && (
              //   <ToolbarAddButton
              //     ouiaId="delete-endpoint-button"
              //     key="delete-endpoint"
              //     defaultLabel={t`Delete`}
              //     onClick={() => handleEndpointDelete()}
              //   />
              // ),
            ]}
          />
        )}
        renderRow={(endpoint, index) => (
          <InstanceEndPointListItem
            isSelected={selected.some((row) => row.id === endpoint.id)}
            onSelect={() => handleSelect(endpoint)}
            isExpanded={expanded.some((row) => row.id === endpoint.id)}
            onExpand={() => handleExpand(endpoint)}
            key={endpoint.id}
            peerEndpoint={endpoint}
            rowIndex={index}
          />
        )}
      />
      {isAddEndpointModalOpen && (
        <AddEndpointModal
          isAddEndpointModalOpen={isAddEndpointModalOpen}
          onClose={() => setisAddEndpointModalOpen(false)}
          title={t`New endpoint`}
          instance={instance}
        />
      )}
      <Toast {...toastProps} />
    </CardBody>
  );
}

export default InstanceEndPointList;
