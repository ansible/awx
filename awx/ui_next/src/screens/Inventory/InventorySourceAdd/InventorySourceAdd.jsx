import React, { useCallback, useEffect } from 'react';
import { useHistory, useParams } from 'react-router-dom';
import { InventorySourcesAPI } from '@api';
import useRequest from '@util/useRequest';
import { Card } from '@patternfly/react-core';
import { CardBody } from '@components/Card';
import InventorySourceForm from '../shared/InventorySourceForm';

function InventorySourceAdd() {
  const history = useHistory();
  const { id } = useParams();

  const { error, request, result } = useRequest(
    useCallback(async values => {
      const { data } = await InventorySourcesAPI.create(values);
      return data;
    }, [])
  );

  useEffect(() => {
    if (result) {
      history.push(
        `/inventories/inventory/${result.inventory}/sources/${result.id}/details`
      );
    }
  }, [result, history]);

  const handleSubmit = async form => {
    const { credential, source_project, ...remainingForm } = form;

    await request({
      credential: credential?.id || null,
      source_project: source_project?.id || null,
      inventory: id,
      ...remainingForm,
    });
  };

  const handleCancel = () => {
    history.push(`/inventories/inventory/${id}/sources`);
  };

  return (
    <Card>
      <CardBody>
        <InventorySourceForm
          onCancel={handleCancel}
          onSubmit={handleSubmit}
          submitError={error}
        />
      </CardBody>
    </Card>
  );
}

export default InventorySourceAdd;
