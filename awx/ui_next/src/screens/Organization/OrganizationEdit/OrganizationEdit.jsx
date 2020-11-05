import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { useHistory } from 'react-router-dom';
import { CardBody } from '../../../components/Card';
import { OrganizationsAPI } from '../../../api';
import { getAddedAndRemoved } from '../../../util/lists';
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
      const {
        added: addedCredentials,
        removed: removedCredentials,
      } = getAddedAndRemoved(
        organization.galaxy_credentials,
        values.galaxy_credentials
      );

      const addedCredentialIds = addedCredentials.map(({ id }) => id);
      const removedCredentialIds = removedCredentials.map(({ id }) => id);

      await OrganizationsAPI.update(organization.id, values);
      await Promise.all(
        groupsToAssociate
          .map(id =>
            OrganizationsAPI.associateInstanceGroup(organization.id, id)
          )
          .concat(
            addedCredentialIds.map(id =>
              OrganizationsAPI.associateGalaxyCredential(organization.id, id)
            )
          )
      );
      await Promise.all(
        groupsToDisassociate
          .map(id =>
            OrganizationsAPI.disassociateInstanceGroup(organization.id, id)
          )
          .concat(
            removedCredentialIds.map(id =>
              OrganizationsAPI.disassociateGalaxyCredential(organization.id, id)
            )
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
      <OrganizationForm
        organization={organization}
        onSubmit={handleSubmit}
        onCancel={handleCancel}
        submitError={formError}
      />
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
