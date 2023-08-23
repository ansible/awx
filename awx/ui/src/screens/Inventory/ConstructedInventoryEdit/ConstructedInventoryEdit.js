import React, { useState, useCallback, useEffect } from 'react';
import { useHistory } from 'react-router-dom';
import { ConstructedInventoriesAPI, InventoriesAPI } from 'api';
import useRequest from 'hooks/useRequest';
import { CardBody } from 'components/Card';
import ContentError from 'components/ContentError';
import ContentLoading from 'components/ContentLoading';
import ConstructedInventoryForm from '../shared/ConstructedInventoryForm';

function isEqual(array1, array2) {
  return (
    array1.length === array2.length &&
    array1.every((element, index) => element.id === array2[index].id)
  );
}

function ConstructedInventoryEdit({ inventory }) {
  const history = useHistory();
  const [submitError, setSubmitError] = useState(null);
  const detailsUrl = `/inventories/constructed_inventory/${inventory.id}/details`;
  const constructedInventoryId = inventory.id;

  const {
    isLoading: isLoadingOptions,
    error: optionsError,
    request: fetchOptions,
    result: options,
  } = useRequest(
    useCallback(
      () =>
        ConstructedInventoriesAPI.readConstructedInventoryOptions(
          constructedInventoryId,
          'PUT'
        ),
      [constructedInventoryId]
    ),
    null
  );

  useEffect(() => {
    fetchOptions();
  }, [fetchOptions]);

  const {
    result: { initialInstanceGroups, initialInputInventories },
    request: fetchedRelatedData,
    error: contentError,
    isLoading,
  } = useRequest(
    useCallback(async () => {
      const [instanceGroupsResponse, inputInventoriesResponse] =
        await Promise.all([
          InventoriesAPI.readInstanceGroups(constructedInventoryId),
          InventoriesAPI.readInputInventories(constructedInventoryId),
        ]);

      return {
        initialInstanceGroups: instanceGroupsResponse.data.results,
        initialInputInventories: inputInventoriesResponse.data.results,
      };
    }, [constructedInventoryId]),
    {
      initialInstanceGroups: [],
      initialInputInventories: [],
      isLoading: true,
    }
  );

  useEffect(() => {
    fetchedRelatedData();
  }, [fetchedRelatedData]);

  const handleSubmit = async (values) => {
    const {
      instanceGroups,
      inputInventories,
      organization,
      ...remainingValues
    } = values;

    remainingValues.organization = organization.id;
    remainingValues.kind = 'constructed';

    try {
      await Promise.all([
        ConstructedInventoriesAPI.update(
          constructedInventoryId,
          remainingValues
        ),
        InventoriesAPI.orderInstanceGroups(
          constructedInventoryId,
          instanceGroups,
          initialInstanceGroups
        ),
      ]);
      /* eslint-disable no-await-in-loop, no-restricted-syntax */
      // Resolve Promises sequentially to avoid race condition
      if (!isEqual(initialInputInventories, values.inputInventories)) {
        for (const inputInventory of initialInputInventories) {
          await InventoriesAPI.disassociateInventory(
            constructedInventoryId,
            inputInventory.id
          );
        }
        for (const inputInventory of values.inputInventories) {
          await InventoriesAPI.associateInventory(
            constructedInventoryId,
            inputInventory.id
          );
        }
      }
      /* eslint-enable no-await-in-loop, no-restricted-syntax */

      history.push(
        `/inventories/constructed_inventory/${constructedInventoryId}/details`
      );
    } catch (error) {
      setSubmitError(error);
    }
  };

  const handleCancel = () => history.push(detailsUrl);

  if (contentError || optionsError) {
    return <ContentError error={contentError || optionsError} />;
  }

  if (isLoading || isLoadingOptions || (!options && !optionsError)) {
    return <ContentLoading />;
  }

  return (
    <CardBody>
      <ConstructedInventoryForm
        onCancel={handleCancel}
        onSubmit={handleSubmit}
        submitError={submitError}
        constructedInventory={inventory}
        instanceGroups={initialInstanceGroups}
        inputInventories={initialInputInventories}
        options={options}
      />
    </CardBody>
  );
}

export default ConstructedInventoryEdit;
