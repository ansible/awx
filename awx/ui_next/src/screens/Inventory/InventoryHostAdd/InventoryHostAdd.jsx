import React, { useState } from 'react';
import { useHistory, useParams } from 'react-router-dom';
import { CardBody } from '@components/Card';
import InventoryHostForm from '../shared/InventoryHostForm';
import { InventoriesAPI } from '@api';

function InventoryHostAdd() {
  const [formError, setFormError] = useState(null);
  const history = useHistory();
  const { id } = useParams();

  const handleSubmit = async values => {
    try {
      const { data: response } = await InventoriesAPI.createHost(id, values);
      history.push(`/inventories/inventory/${id}/hosts/${response.id}/details`);
    } catch (error) {
      setFormError(error);
    }
  };

  const handleCancel = () => {
    history.push(`/inventories/inventory/${id}/hosts`);
  };

  return (
    <CardBody>
      <InventoryHostForm
        handleSubmit={handleSubmit}
        handleCancel={handleCancel}
      />
      {formError ? <div className="formSubmitError">error</div> : ''}
    </CardBody>
  );
}

export default InventoryHostAdd;
