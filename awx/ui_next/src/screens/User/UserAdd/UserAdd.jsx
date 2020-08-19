import React, { useState } from 'react';
import { useHistory } from 'react-router-dom';
import { Card, PageSection } from '@patternfly/react-core';
import { CardBody } from '../../../components/Card';
import UserForm from '../shared/UserForm';
import { OrganizationsAPI } from '../../../api';

function UserAdd() {
  const [formSubmitError, setFormSubmitError] = useState(null);
  const history = useHistory();

  const handleSubmit = async values => {
    setFormSubmitError(null);
    const { organization, ...userValues } = values;
    try {
      const {
        data: { id },
      } = await OrganizationsAPI.createUser(organization, userValues);
      history.push(`/users/${id}/details`);
    } catch (error) {
      setFormSubmitError(error);
    }
  };

  const handleCancel = () => {
    history.push(`/users`);
  };

  return (
    <PageSection>
      <Card>
        <CardBody>
          <UserForm
            handleCancel={handleCancel}
            handleSubmit={handleSubmit}
            submitError={formSubmitError}
          />
        </CardBody>
      </Card>
    </PageSection>
  );
}

export default UserAdd;
