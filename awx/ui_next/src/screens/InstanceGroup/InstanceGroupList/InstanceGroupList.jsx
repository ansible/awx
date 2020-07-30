import React, { useEffect, useCallback } from 'react';
import { useLocation, useRouteMatch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Card, PageSection } from '@patternfly/react-core';

import { InstanceGroupsAPI } from '../../../api';
import { getQSConfig, parseQueryString } from '../../../util/qs';
import useRequest, { useDeleteItems } from '../../../util/useRequest';
import useSelected from '../../../util/useSelected';
import PaginatedDataList, {
  ToolbarDeleteButton,
} from '../../../components/PaginatedDataList';
import ErrorDetail from '../../../components/ErrorDetail';
import AlertModal from '../../../components/AlertModal';
import DatalistToolbar from '../../../components/DataListToolbar';
import AddDropDownButton from '../../../components/AddDropDownButton';

import InstanceGroupListItem from './InstanceGroupListItem';

const QS_CONFIG = getQSConfig('instance_group', {
  page: 1,
  page_size: 20,
});

function modifyInstanceGroups(items = []) {
  return items.map(item => {
    const clonedItem = {
      ...item,
      summary_fields: {
        ...item.summary_fields,
        user_capabilities: {
          ...item.summary_fields.user_capabilities,
        },
      },
    };
    if (clonedItem.name === 'tower') {
      clonedItem.summary_fields.user_capabilities.delete = false;
    }
    return clonedItem;
  });
}

function InstanceGroupList({ i18n }) {
  const location = useLocation();
  const match = useRouteMatch();

  const {
    error: contentError,
    isLoading,
    request: fetchInstanceGroups,
    result: { instanceGroups, instanceGroupsCount, actions },
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
      };
    }, [location]),
    {
      instanceGroups: [],
      instanceGroupsCount: 0,
      actions: {},
    }
  );

  useEffect(() => {
    fetchInstanceGroups();
  }, [fetchInstanceGroups]);

  const { selected, isAllSelected, handleSelect, setSelected } = useSelected(
    instanceGroups
  );

  const modifiedSelected = modifyInstanceGroups(selected);

  const {
    isLoading: deleteLoading,
    deletionError,
    deleteItems: deleteInstanceGroups,
    clearDeletionError,
  } = useDeleteItems(
    useCallback(async () => {
      await Promise.all(
        selected.map(({ id }) => InstanceGroupsAPI.destroy(id))
      );
    }, [selected]),
    {
      qsConfig: QS_CONFIG,
      allItemsSelected: isAllSelected,
      fetchItems: fetchInstanceGroups,
    }
  );

  const handleDelete = async () => {
    await deleteInstanceGroups();
    setSelected([]);
  };

  const canAdd = actions && actions.POST;

  function cannotDelete(item) {
    return !item.summary_fields.user_capabilities.delete;
  }

  const pluralizedItemName = i18n._(t`Instance Groups`);

  let errorMessageDelete = '';

  if (modifiedSelected.some(item => item.name === 'tower')) {
    const itemsUnableToDelete = modifiedSelected
      .filter(cannotDelete)
      .filter(item => item.name !== 'tower')
      .map(item => item.name)
      .join(', ');

    if (itemsUnableToDelete) {
      if (modifiedSelected.some(cannotDelete)) {
        errorMessageDelete = i18n._(
          t`You do not have permission to delete ${pluralizedItemName}: ${itemsUnableToDelete}. `
        );
      }
    }

    if (errorMessageDelete.length > 0) {
      errorMessageDelete = errorMessageDelete.concat('\n');
    }
    errorMessageDelete = errorMessageDelete.concat(
      i18n._(t`The tower instance group cannot be deleted.`)
    );
  }

  const addButtonOptions = [
    {
      label: i18n._(t`Instance group`),
      url: '/instance_groups/add',
    },
    {
      label: i18n._(t`Container group`),
      url: '/instance_groups/container_group/add',
    },
  ];

  const addButton = (
    <AddDropDownButton key="add" dropdownItems={addButtonOptions} />
  );

  const getDetailUrl = item => {
    return item.is_containerized
      ? `${match.url}/container_group/${item.id}/details`
      : `${match.url}/${item.id}/details`;
  };

  return (
    <>
      <PageSection>
        <Card>
          <PaginatedDataList
            contentError={contentError}
            hasContentLoading={isLoading || deleteLoading}
            items={instanceGroups}
            itemCount={instanceGroupsCount}
            pluralizedItemName={pluralizedItemName}
            qsConfig={QS_CONFIG}
            onRowClick={handleSelect}
            renderToolbar={props => (
              <DatalistToolbar
                {...props}
                showSelectAll
                showExpandCollapse
                isAllSelected={isAllSelected}
                onSelectAll={isSelected =>
                  setSelected(isSelected ? [...instanceGroups] : [])
                }
                qsConfig={QS_CONFIG}
                additionalControls={[
                  ...(canAdd ? [addButton] : []),
                  <ToolbarDeleteButton
                    key="delete"
                    onDelete={handleDelete}
                    itemsToDelete={modifiedSelected}
                    pluralizedItemName={i18n._(t`Instance Groups`)}
                    errorMessage={errorMessageDelete}
                  />,
                ]}
              />
            )}
            renderItem={instanceGroup => (
              <InstanceGroupListItem
                key={instanceGroup.id}
                value={instanceGroup.name}
                instanceGroup={instanceGroup}
                detailUrl={getDetailUrl(instanceGroup)}
                onSelect={() => handleSelect(instanceGroup)}
                isSelected={selected.some(row => row.id === instanceGroup.id)}
              />
            )}
            emptyStateControls={canAdd && addButton}
          />
        </Card>
      </PageSection>
      <AlertModal
        aria-label={i18n._(t`Deletion error`)}
        isOpen={deletionError}
        onClose={clearDeletionError}
        title={i18n._(t`Error`)}
        variant="error"
      >
        {i18n._(t`Failed to delete one or more instance groups.`)}
        <ErrorDetail error={deletionError} />
      </AlertModal>
    </>
  );
}

export default withI18n()(InstanceGroupList);
