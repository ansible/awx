import React, { useEffect, useCallback } from 'react';
import { useLocation, useRouteMatch, Link } from 'react-router-dom';

import { t, Plural } from '@lingui/macro';
import { Card, PageSection, DropdownItem } from '@patternfly/react-core';

import { InstanceGroupsAPI, SettingsAPI } from 'api';
import { getQSConfig, parseQueryString } from 'util/qs';
import useRequest, { useDeleteItems } from 'hooks/useRequest';
import useSelected from 'hooks/useSelected';
import PaginatedTable, {
  HeaderRow,
  HeaderCell,
  ToolbarAddButton,
  ToolbarDeleteButton,
} from 'components/PaginatedTable';
import ErrorDetail from 'components/ErrorDetail';
import AlertModal from 'components/AlertModal';
import DatalistToolbar from 'components/DataListToolbar';
import AddDropDownButton from 'components/AddDropDownButton';
import { relatedResourceDeleteRequests } from 'util/getRelatedResourceDeleteDetails';
import InstanceGroupListItem from './InstanceGroupListItem';

const QS_CONFIG = getQSConfig('instance-group', {
  page: 1,
  page_size: 20,
});

function modifyInstanceGroups(
  items = [],
  defaultControlPlane,
  defaultExecution
) {
  return items.map((item) => {
    const clonedItem = {
      ...item,
      summary_fields: {
        ...item.summary_fields,
        user_capabilities: {
          ...item.summary_fields.user_capabilities,
        },
      },
    };
    if (clonedItem.name === (defaultControlPlane || defaultExecution)) {
      clonedItem.summary_fields.user_capabilities.delete = false;
    }
    return clonedItem;
  });
}

function InstanceGroupList({
  isKubernetes,
  isSettingsRequestLoading,
  settingsRequestError,
}) {
  const location = useLocation();
  const match = useRouteMatch();
  const {
    error: protectedItemsError,
    isloading: isLoadingProtectedItems,
    request: fetchProtectedItems,
    result: { defaultControlPlane, defaultExecution },
  } = useRequest(
    useCallback(async () => {
      const {
        data: {
          DEFAULT_CONTROL_PLANE_QUEUE_NAME,
          DEFAULT_EXECUTION_QUEUE_NAME,
        },
      } = await SettingsAPI.readAll();
      return {
        defaultControlPlane: DEFAULT_CONTROL_PLANE_QUEUE_NAME,
        defaultExecution: DEFAULT_EXECUTION_QUEUE_NAME,
      };
    }, []),
    { defaultControlPlane: '', defaultExecution: '' }
  );

  useEffect(() => {
    fetchProtectedItems();
  }, [fetchProtectedItems]);

  const {
    error: contentError,
    isLoading,
    request: fetchInstanceGroups,
    result: {
      instanceGroups,
      instanceGroupsCount,
      actions,
      relatedSearchableKeys,
      searchableKeys,
    },
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);

      const [response, responseActions] = await Promise.all([
        InstanceGroupsAPI.read(params),
        InstanceGroupsAPI.readOptions(),
      ]);

      return {
        instanceGroups: response.data.results,
        instanceGroupsCount: response.data.count,
        actions: responseActions.data.actions,
        relatedSearchableKeys: (
          responseActions?.data?.related_search_fields || []
        ).map((val) => val.slice(0, -8)),
        searchableKeys: Object.keys(
          responseActions.data.actions?.GET || {}
        ).filter((key) => responseActions.data.actions?.GET[key].filterable),
      };
    }, [location]),
    {
      instanceGroups: [],
      instanceGroupsCount: 0,
      actions: {},
      relatedSearchableKeys: [],
      searchableKeys: [],
    }
  );

  useEffect(() => {
    fetchInstanceGroups();
  }, [fetchInstanceGroups]);

  const { selected, isAllSelected, handleSelect, clearSelected, selectAll } =
    useSelected(instanceGroups);

  const modifiedSelected = modifyInstanceGroups(
    selected,
    defaultControlPlane,
    defaultExecution
  );

  const {
    isLoading: deleteLoading,
    deletionError,
    deleteItems: deleteInstanceGroups,
    clearDeletionError,
  } = useDeleteItems(
    useCallback(
      () =>
        Promise.all(selected.map(({ id }) => InstanceGroupsAPI.destroy(id))),
      [selected]
    ),
    {
      qsConfig: QS_CONFIG,
      allItemsSelected: isAllSelected,
      fetchItems: fetchInstanceGroups,
    }
  );

  const handleDelete = async () => {
    await deleteInstanceGroups();
    clearSelected();
  };

  const canAdd = actions && actions.POST;

  function cannotDelete(item) {
    return (
      !item.summary_fields.user_capabilities.delete ||
      item.name === defaultExecution ||
      item.name === defaultControlPlane
    );
  }

  const pluralizedItemName = t`Instance Groups`;

  let errorMessageDelete = '';
  const notdeletedable = selected.filter(
    (i) => i.name === defaultControlPlane || i.name === defaultExecution
  );

  if (notdeletedable.length) {
    errorMessageDelete = (
      <Plural
        value={notdeletedable.length}
        one="The following Instance Group cannot be deleted"
        other="The following Instance Groups cannot be deleted"
      />
    );
  }

  const addContainerGroup = t`Add container group`;
  const addInstanceGroup = t`Add instance group`;

  const addButton =
    !isSettingsRequestLoading && !isKubernetes ? (
      <AddDropDownButton
        ouiaId="add-instance-group-button"
        key="add"
        dropdownItems={[
          <DropdownItem
            ouiaId="add-container-group-item"
            to="/instance_groups/container_group/add"
            component={Link}
            key={addContainerGroup}
            aria-label={addContainerGroup}
          >
            {addContainerGroup}
          </DropdownItem>,
          <DropdownItem
            ouiaId="add-instance-group-item"
            to="/instance_groups/add"
            component={Link}
            key={addInstanceGroup}
            aria-label={addInstanceGroup}
          >
            {addInstanceGroup}
          </DropdownItem>,
        ]}
      />
    ) : (
      <ToolbarAddButton
        key="add"
        ouiaId="add-container-group-button"
        linkTo={`${match.url}/container_group/add`}
      />
    );

  const getDetailUrl = (item) =>
    item.is_container_group
      ? `${match.url}/container_group/${item.id}/details`
      : `${match.url}/${item.id}/details`;
  const deleteDetailsRequests = relatedResourceDeleteRequests.instanceGroup(
    selected[0]
  );
  return (
    <>
      <PageSection>
        <Card>
          <PaginatedTable
            contentError={
              contentError || settingsRequestError || protectedItemsError
            }
            hasContentLoading={
              isLoading ||
              deleteLoading ||
              isSettingsRequestLoading ||
              isLoadingProtectedItems
            }
            items={instanceGroups}
            itemCount={instanceGroupsCount}
            pluralizedItemName={pluralizedItemName}
            qsConfig={QS_CONFIG}
            clearSelected={clearSelected}
            toolbarSearchableKeys={searchableKeys}
            toolbarRelatedSearchableKeys={relatedSearchableKeys}
            renderToolbar={(props) => (
              <DatalistToolbar
                {...props}
                isAllSelected={isAllSelected}
                onSelectAll={selectAll}
                qsConfig={QS_CONFIG}
                additionalControls={[
                  ...(canAdd ? [addButton] : []),
                  <ToolbarDeleteButton
                    key="delete"
                    onDelete={handleDelete}
                    cannotDelete={cannotDelete}
                    itemsToDelete={modifiedSelected}
                    pluralizedItemName={t`Instance Groups`}
                    errorMessage={errorMessageDelete}
                    deleteDetailsRequests={deleteDetailsRequests}
                    deleteMessage={
                      <Plural
                        value={selected.length}
                        one="This instance group is currently being by other resources. Are you sure you want to delete it?"
                        other="Deleting these instance groups could impact other resources that rely on them. Are you sure you want to delete anyway?"
                      />
                    }
                  />,
                ]}
              />
            )}
            headerRow={
              <HeaderRow qsConfig={QS_CONFIG}>
                <HeaderCell sortKey="name">{t`Name`}</HeaderCell>
                <HeaderCell>{t`Type`}</HeaderCell>
                <HeaderCell>{t`Running Jobs`}</HeaderCell>
                <HeaderCell>{t`Total Jobs`}</HeaderCell>
                <HeaderCell>{t`Instances`}</HeaderCell>
                <HeaderCell>{t`Capacity`}</HeaderCell>
                <HeaderCell>{t`Actions`}</HeaderCell>
              </HeaderRow>
            }
            renderRow={(instanceGroup, index) => (
              <InstanceGroupListItem
                key={instanceGroup.id}
                value={instanceGroup.name}
                instanceGroup={instanceGroup}
                detailUrl={getDetailUrl(instanceGroup)}
                onSelect={() => handleSelect(instanceGroup)}
                isSelected={selected.some((row) => row.id === instanceGroup.id)}
                rowIndex={index}
              />
            )}
            emptyStateControls={canAdd && addButton}
          />
        </Card>
      </PageSection>
      <AlertModal
        aria-label={t`Deletion error`}
        isOpen={deletionError}
        onClose={clearDeletionError}
        title={t`Error`}
        variant="error"
      >
        {t`Failed to delete one or more instance groups.`}
        <ErrorDetail error={deletionError} />
      </AlertModal>
    </>
  );
}

export default InstanceGroupList;
