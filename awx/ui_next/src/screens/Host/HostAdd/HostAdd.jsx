import React, { useState } from 'react';
import { useHistory, useRouteMatch } from 'react-router-dom';
import { t } from '@lingui/macro';
import { withI18n } from '@lingui/react';
import { CardBody } from '@components/Card';
import ErrorDetail from '@components/ErrorDetail';
import AlertModal from '@components/AlertModal';
import { HostsAPI } from '@api';
import HostForm from '../shared';

function HostAdd({ i18n }) {
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
      // check for field-specific errors from API
      if (error.response?.data && typeof error.response.data === 'object') {
        throw error.response.data;
      }
      setFormError(error);
    }
  };

  const handleCancel = () => {
    history.push(`${url}`);
  };

  return (
    <CardBody>
      <HostForm handleSubmit={handleSubmit} handleCancel={handleCancel} />
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

export default withI18n()(HostAdd);
