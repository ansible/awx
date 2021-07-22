import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { useHistory } from 'react-router-dom';
import { CardBody } from 'components/Card';
import { OrganizationsAPI } from 'api';
import OrganizationForm from '../shared/OrganizationForm';

const isEqual = (array1, array2) =>
  array1.length === array2.length &&
  array1.every((element, index) => element.id === array2[index].id);

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
      await OrganizationsAPI.update(organization.id, {
        ...values,
        default_environment: values.default_environment?.id || null,
      });
      await OrganizationsAPI.orderInstanceGroups(
        organization.id,
        groupsToAssociate,
        groupsToDisassociate
      );

      /* eslint-disable no-await-in-loop, no-restricted-syntax */
      // Resolve Promises sequentially to avoid race condition
      if (
        !isEqual(organization.galaxy_credentials, values.galaxy_credentials)
      ) {
        for (const credential of organization.galaxy_credentials) {
          await OrganizationsAPI.disassociateGalaxyCredential(
            organization.id,
            credential.id
          );
        }
        for (const credential of values.galaxy_credentials) {
          await OrganizationsAPI.associateGalaxyCredential(
            organization.id,
            credential.id
          );
        }
      }
      /* eslint-enable no-await-in-loop, no-restricted-syntax */
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

export { OrganizationEdit as _OrganizationEdit };
export default OrganizationEdit;
