import React, { useState } from 'react';
import { useHistory, useRouteMatch } from 'react-router-dom';
import { CardBody } from '@components/Card';
import { HostsAPI } from '@api';
import HostForm from '../shared';

function HostAdd() {
  const [formError, setFormError] = useState(null);
  const history = useHistory();
  const hostsMatch = useRouteMatch('/hosts');
  const inventoriesMatch = useRouteMatch('/inventories/inventory/:id/hosts');
  const url = hostsMatch ? hostsMatch.url : inventoriesMatch.url;

  const handleSubmit = async formData => {
    const values = {
      ...formData,
      inventory: inventoriesMatch
        ? inventoriesMatch.params.id
        : formData.inventory,
    };

    try {
      const { data: response } = await HostsAPI.create(values);
      history.push(`${url}/${response.id}/details`);
    } catch (error) {
      setFormError(error);
    }
  };

  const handleCancel = () => {
    history.push(`${url}`);
  };

  return (
    <CardBody>
      <HostForm
        handleSubmit={handleSubmit}
        handleCancel={handleCancel}
        submitError={formError}
      />
    </CardBody>
  );
}

export default HostAdd;
