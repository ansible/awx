import React, { useState } from 'react';
import { useHistory } from 'react-router-dom';
import { PageSection, Card } from '@patternfly/react-core';
import { CardBody } from 'components/Card';

import { InventoriesAPI } from 'api';
import InventoryForm from '../shared/InventoryForm';

function InventoryAdd() {
  const [error, setError] = useState(null);
  const history = useHistory();

  const handleCancel = () => {
    history.push('/inventories');
  };

  async function submitLabels(inventoryId, orgId, labels = []) {
    const associationPromises = labels.map((label) =>
      InventoriesAPI.associateLabel(inventoryId, label, orgId)
    );

    return Promise.all([...associationPromises]);
  }

  const handleSubmit = async (values) => {
    const { instanceGroups, organization, ...remainingValues } = values;
    try {
      const {
        data: { id: inventoryId },
      } = await InventoriesAPI.create({
        organization: organization.id,
        ...remainingValues,
      });
      /* eslint-disable no-await-in-loop, no-restricted-syntax */
      // Resolve Promises sequentially to maintain order and avoid race condition

      await submitLabels(inventoryId, values.organization?.id, values.labels);
      for (const group of instanceGroups) {
        await InventoriesAPI.associateInstanceGroup(inventoryId, group.id);
      }
      /* eslint-enable no-await-in-loop, no-restricted-syntax */
      const url = history.location.pathname.startsWith(
        '/inventories/smart_inventory'
      )
        ? `/inventories/smart_inventory/${inventoryId}/details`
        : `/inventories/inventory/${inventoryId}/details`;

      history.push(`${url}`);
    } catch (err) {
      setError(err);
    }
  };

  return (
    <PageSection>
      <Card>
        <CardBody>
          <InventoryForm
            onCancel={handleCancel}
            onSubmit={handleSubmit}
            submitError={error}
          />
        </CardBody>
      </Card>
    </PageSection>
  );
}

export { InventoryAdd as _InventoryAdd };
export default InventoryAdd;
