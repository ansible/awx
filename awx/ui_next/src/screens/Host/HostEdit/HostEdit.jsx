import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { useHistory, useRouteMatch } from 'react-router-dom';
import { CardBody } from '@components/Card';
import { HostsAPI } from '@api';
import HostForm from '../shared';

function HostEdit({ host }) {
  const [formError, setFormError] = useState(null);
  const hostsMatch = useRouteMatch('/hosts/:id/edit');
  const inventoriesMatch = useRouteMatch(
    '/inventories/inventory/:id/hosts/:hostId/edit'
  );
  const history = useHistory();
  let detailsUrl;

  if (hostsMatch) {
    detailsUrl = `/hosts/${hostsMatch.params.id}/details`;
  }

  if (inventoriesMatch) {
    const kind =
      host.summary_fields.inventory.kind === 'smart'
        ? 'smart_inventory'
        : 'inventory';
    detailsUrl = `/inventories/${kind}/${inventoriesMatch.params.id}/hosts/${inventoriesMatch.params.hostId}/details`;
  }

  const handleSubmit = async values => {
    try {
      await HostsAPI.update(host.id, values);
      history.push(detailsUrl);
    } catch (error) {
      console.log('caught:', error);
      // // check for field-specific errors from API
      // if (error.response?.data && typeof error.response.data === 'object') {
      //   throw error.response.data;
      // }
      setFormError(error);
    }
  };
  console.log('render:', formError);

  const handleCancel = () => {
    history.push(detailsUrl);
  };

  return (
    <CardBody>
      <HostForm
        host={host}
        handleSubmit={handleSubmit}
        handleCancel={handleCancel}
        submitError={formError}
      />
    </CardBody>
  );
}

HostEdit.propTypes = {
  host: PropTypes.shape().isRequired,
};

export default HostEdit;
