import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { useHistory } from 'react-router-dom';
import { PageSection, Card } from '@patternfly/react-core';

import { OrganizationsAPI } from '@api';
import { Config } from '@contexts/Config';
import { CardBody } from '@components/Card';
import OrganizationForm from '../shared/OrganizationForm';

function OrganizationAdd() {
  const history = useHistory();
  const [formError, setFormError] = useState(null);

  const handleSubmit = async (values, groupsToAssociate) => {
    try {
      const { data: response } = await OrganizationsAPI.create(values);
      await Promise.all(
        groupsToAssociate.map(id =>
          OrganizationsAPI.associateInstanceGroup(response.id, id)
        )
      );
      history.push(`/organizations/${response.id}`);
    } catch (error) {
      setFormError(error);
    }
  };

  const handleCancel = () => {
    history.push('/organizations');
  };

  return (
    <PageSection>
      <Card>
        <CardBody>
          <Config>
            {({ me }) => (
              <OrganizationForm
                onSubmit={handleSubmit}
                onCancel={handleCancel}
                me={me || {}}
                submitError={formError}
              />
            )}
          </Config>
        </CardBody>
      </Card>
    </PageSection>
  );
}

OrganizationAdd.contextTypes = {
  custom_virtualenvs: PropTypes.arrayOf(PropTypes.string),
};

export { OrganizationAdd as _OrganizationAdd };
export default OrganizationAdd;
