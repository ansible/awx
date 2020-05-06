import React, { useState } from 'react';
import { useHistory } from 'react-router-dom';
import { CardBody } from '../../../components/Card';
import HostForm from '../../../components/HostForm';

import { HostsAPI } from '../../../api';

function InventoryHostAdd({ inventory }) {
  const [formError, setFormError] = useState(null);
  const hostsUrl = `/inventories/inventory/${inventory.id}/hosts`;
  const history = useHistory();

  const handleSubmit = async formData => {
    try {
      const values = {
        ...formData,
        inventory: inventory.id,
      };
      const { data: response } = await HostsAPI.create(values);
      history.push(`${hostsUrl}/${response.id}/details`);
    } catch (error) {
      setFormError(error);
    }
  };

  const handleCancel = () => {
    history.push(hostsUrl);
  };

  return (
    <CardBody>
      <HostForm
        handleSubmit={handleSubmit}
        handleCancel={handleCancel}
        isInventoryVisible={false}
        submitError={formError}
      />
    </CardBody>
  );
}

export default InventoryHostAdd;
