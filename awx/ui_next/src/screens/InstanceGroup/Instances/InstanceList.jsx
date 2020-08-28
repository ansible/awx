import React, { useCallback, useEffect, useState } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { useLocation, useParams } from 'react-router-dom';
import 'styled-components/macro';

import DataListToolbar from '../../../components/DataListToolbar';
import PaginatedDataList, {
  ToolbarAddButton,
} from '../../../components/PaginatedDataList';
import DisassociateButton from '../../../components/DisassociateButton';
import AssociateModal from '../../../components/AssociateModal';
import AlertModal from '../../../components/AlertModal';
import ErrorDetail from '../../../components/ErrorDetail';

import useRequest, {
  useDeleteItems,
  useDismissableError,
} from '../../../util/useRequest';
import useSelected from '../../../util/useSelected';
import { InstanceGroupsAPI, InstancesAPI } from '../../../api';
import { getQSConfig, parseQueryString, mergeParams } from '../../../util/qs';

import InstanceListItem from './InstanceListItem';

const QS_CONFIG = getQSConfig('instance', {
  page: 1,
  page_size: 20,
  order_by: 'hostname',
});

function InstanceList({ i18n }) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const location = useLocation();
  const { id: instanceGroupId } = useParams();

  const {
    result: {
      instances,
      count,
      actions,
      relatedSearchableKeys,
      searchableKeys,
    },
    error: contentError,
    isLoading,
    request: fetchInstances,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);
      const [response, responseActions] = await Promise.all([
        InstanceGroupsAPI.readInstances(instanceGroupId, params),
        InstanceGroupsAPI.readInstanceOptions(instanceGroupId),
      ]);
      return {
        instances: response.data.results,
        count: response.data.count,
        actions: responseActions.data.actions,
        relatedSearchableKeys: (
          responseActions?.data?.related_search_fields || []
        ).map(val => val.slice(0, -8)),
        searchableKeys: Object.keys(
          responseActions.data.actions?.GET || {}
        ).filter(key => responseActions.data.actions?.GET[key].filterable),
      };
    }, [location.search, instanceGroupId]),
    {
      instances: [],
      count: 0,
      actions: {},
      relatedSearchableKeys: [],
      searchableKeys: [],
    }
  );

  const { selected, isAllSelected, handleSelect, setSelected } = useSelected(
    instances
  );

  useEffect(() => {
    fetchInstances();
  }, [fetchInstances]);

  const {
    isLoading: isDisassociateLoading,
    deleteItems: disassociateInstances,
    deletionError: disassociateError,
  } = useDeleteItems(
    useCallback(async () => {
      return Promise.all(
        selected.map(instance =>
          InstanceGroupsAPI.disassociateInstance(instanceGroupId, instance.id)
        )
      );
    }, [instanceGroupId, selected]),
    {
      qsConfig: QS_CONFIG,
      allItemsSelected: isAllSelected,
      fetchItems: fetchInstances,
    }
  );

  const { request: handleAssociate, error: associateError } = useRequest(
    useCallback(
      async instancesToAssociate => {
        await Promise.all(
          instancesToAssociate.map(instance =>
            InstanceGroupsAPI.associateInstance(instanceGroupId, instance.id)
          )
        );
        fetchInstances();
      },
      [instanceGroupId, fetchInstances]
    )
  );

  const handleDisassociate = async () => {
    await disassociateInstances();
    setSelected([]);
  };

  const { error, dismissError } = useDismissableError(
    associateError || disassociateError
  );

  const canAdd =
    actions && Object.prototype.hasOwnProperty.call(actions, 'POST');

  const fetchInstancesToAssociate = useCallback(
    params => {
      return InstancesAPI.read(
        mergeParams(params, { not__rampart_groups__id: instanceGroupId })
      );
    },
    [instanceGroupId]
  );

  const readInstancesOptions = () =>
    InstanceGroupsAPI.readInstanceOptions(instanceGroupId);

  return (
    <>
      <PaginatedDataList
        contentError={contentError}
        hasContentLoading={isLoading || isDisassociateLoading}
        items={instances}
        itemCount={count}
        pluralizedItemName={i18n._(t`Instances`)}
        qsConfig={QS_CONFIG}
        onRowClick={handleSelect}
        toolbarSearchableKeys={searchableKeys}
        toolbarRelatedSearchableKeys={relatedSearchableKeys}
        toolbarSearchColumns={[
          {
            name: i18n._(t`Name`),
            key: 'hostname',
            isDefault: true,
          },
        ]}
        toolbarSortColumns={[
          {
            name: i18n._(t`Name`),
            key: 'hostname',
          },
        ]}
        renderToolbar={props => (
          <DataListToolbar
            {...props}
            showSelectAll
            isAllSelected={isAllSelected}
            onSelectAll={isSelected =>
              setSelected(isSelected ? [...instances] : [])
            }
            qsConfig={QS_CONFIG}
            additionalControls={[
              ...(canAdd
                ? [
                    <ToolbarAddButton
                      key="associate"
                      onClick={() => setIsModalOpen(true)}
                      defaultLabel={i18n._(t`Associate`)}
                    />,
                  ]
                : []),
              <DisassociateButton
                verifyCannotDisassociate={false}
                key="disassociate"
                onDisassociate={handleDisassociate}
                itemsToDisassociate={selected}
                modalTitle={i18n._(
                  t`Disassociate instance from instance group?`
                )}
              />,
            ]}
            emptyStateControls={
              canAdd ? (
                <ToolbarAddButton
                  key="add"
                  onClick={() => setIsModalOpen(true)}
                />
              ) : null
            }
          />
        )}
        renderItem={instance => (
          <InstanceListItem
            key={instance.id}
            value={instance.hostname}
            instance={instance}
            onSelect={() => handleSelect(instance)}
            isSelected={selected.some(row => row.id === instance.id)}
            fetchInstances={fetchInstances}
          />
        )}
      />
      {isModalOpen && (
        <AssociateModal
          header={i18n._(t`Instances`)}
          fetchRequest={fetchInstancesToAssociate}
          isModalOpen={isModalOpen}
          onAssociate={handleAssociate}
          onClose={() => setIsModalOpen(false)}
          title={i18n._(t`Select Instances`)}
          optionsRequest={readInstancesOptions}
          displayKey="hostname"
        />
      )}
      {error && (
        <AlertModal
          isOpen={error}
          onClose={dismissError}
          title={i18n._(t`Error!`)}
          variant="error"
        >
          {associateError
            ? i18n._(t`Failed to associate.`)
            : i18n._(t`Failed to disassociate one or more instances.`)}
          <ErrorDetail error={error} />
        </AlertModal>
      )}
    </>
  );
}

export default withI18n()(InstanceList);
