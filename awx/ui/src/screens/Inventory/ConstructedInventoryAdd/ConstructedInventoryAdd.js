import React, { useState } from 'react';
import { useHistory } from 'react-router-dom';
import { Card, PageSection } from '@patternfly/react-core';
import { ConstructedInventoriesAPI, InventoriesAPI } from 'api';
import { CardBody } from 'components/Card';
import ConstructedInventoryForm from '../shared/ConstructedInventoryForm';

function ConstructedInventoryAdd() {
  const history = useHistory();
  const [submitError, setSubmitError] = useState(null);

  const handleCancel = () => {
    history.push('/inventories');
  };

  const handleSubmit = async (values) => {
    try {
      const {
        data: { id: inventoryId },
      } = await ConstructedInventoriesAPI.create({
        ...values,
        organization: values.organization?.id,
        kind: 'constructed',
      });
      /* eslint-disable no-await-in-loop, no-restricted-syntax */
      for (const inputInventory of values.inputInventories) {
        await InventoriesAPI.associateInventory(inventoryId, inputInventory.id);
      }
      for (const instanceGroup of values.instanceGroups) {
        await InventoriesAPI.associateInstanceGroup(
          inventoryId,
          instanceGroup.id
        );
      }
      /* eslint-enable no-await-in-loop, no-restricted-syntax */

      history.push(`/inventories/constructed_inventory/${inventoryId}/details`);
    } catch (error) {
      setSubmitError(error);
    }
  };

  return (
    <PageSection>
      <Card>
        <CardBody>
          <ConstructedInventoryForm
            onCancel={handleCancel}
            onSubmit={handleSubmit}
            submitError={submitError}
          />
        </CardBody>
      </Card>
    </PageSection>
  );
}

export default ConstructedInventoryAdd;
