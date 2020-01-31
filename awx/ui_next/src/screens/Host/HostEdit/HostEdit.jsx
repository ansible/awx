import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { useHistory, useRouteMatch } from 'react-router-dom';
import { t } from '@lingui/macro';
import { withI18n } from '@lingui/react';
import { CardBody } from '@components/Card';
import ErrorDetail from '@components/ErrorDetail';
import AlertModal from '@components/AlertModal';
import { HostsAPI } from '@api';
import HostForm from '../shared';

function HostEdit({ host, i18n }) {
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
      if (error.response?.data) {
        throw error.response.data;
      }
      setFormError(error);
    }
  };

  const handleCancel = () => {
    history.push(detailsUrl);
  };

  return (
    <CardBody>
      <HostForm
        host={host}
        handleSubmit={handleSubmit}
        handleCancel={handleCancel}
      />
      {formError && (
        <AlertModal
          variant="danger"
          title={i18n._(t`Error!`)}
          isOpen={formError}
          onClose={() => setFormError(null)}
        >
          {i18n._(t`An error occurred when saving Host`)}
          <ErrorDetail error={formError} />
        </AlertModal>
      )}
    </CardBody>
  );
}

HostEdit.propTypes = {
  host: PropTypes.shape().isRequired,
};

export { HostEdit as _HostEdit };
export default withI18n()(HostEdit);
