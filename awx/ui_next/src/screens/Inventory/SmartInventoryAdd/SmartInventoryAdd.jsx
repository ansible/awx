import React, { useCallback, useEffect } from 'react';
import { useHistory } from 'react-router-dom';
import { Card, PageSection } from '@patternfly/react-core';
import { CardBody } from '../../../components/Card';
import SmartInventoryForm from '../shared/SmartInventoryForm';
import useRequest from '../../../util/useRequest';
import { InventoriesAPI } from '../../../api';

function SmartInventoryAdd() {
  const history = useHistory();

  const {
    error: submitError,
    request: submitRequest,
    result: inventoryId,
  } = useRequest(
    useCallback(async (values, groupsToAssociate) => {
      const {
        data: { id: invId },
      } = await InventoriesAPI.create(values);

      await Promise.all(
        groupsToAssociate.map(({ id }) =>
          InventoriesAPI.associateInstanceGroup(invId, id)
        )
      );
      return invId;
    }, [])
  );

  const handleSubmit = async form => {
    const { instance_groups, organization, ...remainingForm } = form;

    await submitRequest(
      {
        organization: organization?.id,
        ...remainingForm,
      },
      instance_groups
    );
  };

  const handleCancel = () => {
    history.push({
      pathname: '/inventories',
      search: '',
    });
  };

  useEffect(() => {
    if (inventoryId) {
      history.push({
        pathname: `/inventories/smart_inventory/${inventoryId}/details`,
        search: '',
      });
    }
  }, [inventoryId, history]);

  return (
    <PageSection>
      <Card>
        <CardBody>
          <SmartInventoryForm
            onCancel={handleCancel}
            onSubmit={handleSubmit}
            submitError={submitError}
          />
        </CardBody>
      </Card>
    </PageSection>
  );
}

export default SmartInventoryAdd;
