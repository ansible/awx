import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { useHistory } from 'react-router-dom';
import { CardBody } from '@components/Card';
import { OrganizationsAPI } from '@api';
import { Config } from '@contexts/Config';

import OrganizationForm from '../shared/OrganizationForm';

function OrganizationEdit({ organization }) {
  const detailsUrl = `/organizations/${organization.id}/details`;
  const history = useHistory();
  const [formError, setFormError] = useState(null);

  const handleSubmit = async (
    values,
    groupsToAssociate,
    groupsToDisassociate
  ) => {
    try {
      await OrganizationsAPI.update(organization.id, values);
      await Promise.all(
        groupsToAssociate.map(id =>
          OrganizationsAPI.associateInstanceGroup(organization.id, id)
        )
      );
      await Promise.all(
        groupsToDisassociate.map(id =>
          OrganizationsAPI.disassociateInstanceGroup(organization.id, id)
        )
      );
      history.push(detailsUrl);
    } catch (error) {
      setFormError(error);
    }
  };

  const handleCancel = () => {
    history.push(detailsUrl);
  };

  return (
    <CardBody>
      <Config>
        {({ me }) => (
          <OrganizationForm
            organization={organization}
            onSubmit={handleSubmit}
            onCancel={handleCancel}
            me={me || {}}
            submitError={formError}
          />
        )}
      </Config>
    </CardBody>
  );
}

OrganizationEdit.propTypes = {
  organization: PropTypes.shape().isRequired,
};

OrganizationEdit.contextTypes = {
  custom_virtualenvs: PropTypes.arrayOf(PropTypes.string),
};

export { OrganizationEdit as _OrganizationEdit };
export default OrganizationEdit;
