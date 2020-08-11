import React, { useCallback, useEffect } from 'react';
import { useHistory } from 'react-router-dom';
import { Inventory } from '../../../types';
import { getAddedAndRemoved } from '../../../util/lists';
import useRequest from '../../../util/useRequest';
import { InventoriesAPI } from '../../../api';
import { CardBody } from '../../../components/Card';
import ContentError from '../../../components/ContentError';
import ContentLoading from '../../../components/ContentLoading';
import SmartInventoryForm from '../shared/SmartInventoryForm';

function SmartInventoryEdit({ inventory }) {
  const history = useHistory();
  const detailsUrl = `/inventories/smart_inventory/${inventory.id}/details`;

  const {
    error: contentError,
    isLoading: hasContentLoading,
    request: fetchInstanceGroups,
    result: instanceGroups,
  } = useRequest(
    useCallback(async () => {
      const {
        data: { results },
      } = await InventoriesAPI.readInstanceGroups(inventory.id);
      return results;
    }, [inventory.id]),
    []
  );

  useEffect(() => {
    fetchInstanceGroups();
  }, [fetchInstanceGroups]);

  const {
    error: submitError,
    request: submitRequest,
    result: submitResult,
  } = useRequest(
    useCallback(
      async (values, groupsToAssociate, groupsToDisassociate) => {
        const { data } = await InventoriesAPI.update(inventory.id, values);
        await Promise.all(
          groupsToAssociate.map(id =>
            InventoriesAPI.associateInstanceGroup(inventory.id, id)
          )
        );
        await Promise.all(
          groupsToDisassociate.map(id =>
            InventoriesAPI.disassociateInstanceGroup(inventory.id, id)
          )
        );
        return data;
      },
      [inventory.id]
    )
  );

  useEffect(() => {
    if (submitResult) {
      history.push({
        pathname: detailsUrl,
        search: '',
      });
    }
  }, [submitResult, detailsUrl, history]);

  const handleSubmit = async form => {
    const { instance_groups, organization, ...remainingForm } = form;

    const { added, removed } = getAddedAndRemoved(
      instanceGroups,
      instance_groups
    );
    const addedIds = added.map(({ id }) => id);
    const removedIds = removed.map(({ id }) => id);

    await submitRequest(
      {
        organization: organization?.id,
        ...remainingForm,
      },
      addedIds,
      removedIds
    );
  };

  const handleCancel = () => {
    history.push({
      pathname: detailsUrl,
      search: '',
    });
  };

  if (hasContentLoading) {
    return <ContentLoading />;
  }

  if (contentError) {
    return <ContentError error={contentError} />;
  }

  return (
    <CardBody>
      <SmartInventoryForm
        inventory={inventory}
        instanceGroups={instanceGroups}
        onCancel={handleCancel}
        onSubmit={handleSubmit}
        submitError={submitError}
      />
    </CardBody>
  );
}

SmartInventoryEdit.propTypes = {
  inventory: Inventory.isRequired,
};

export default SmartInventoryEdit;
