import React, { useState } from 'react';
import { useHistory } from 'react-router-dom';
import styled from 'styled-components';
import { Card as _Card, PageSection } from '@patternfly/react-core';
import { CardBody } from '@components/Card';
import UserForm from '../shared/UserForm';
import { UsersAPI } from '@api';

const Card = styled(_Card)`
  --pf-c-card--child--PaddingLeft: 0;
  --pf-c-card--child--PaddingRight: 0;
`;

function UserAdd() {
  const [formSubmitError, setFormSubmitError] = useState(null);
  const history = useHistory();

  const handleSubmit = async values => {
    setFormSubmitError(null);
    try {
      const {
        data: { id },
      } = await UsersAPI.create(values);
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
          <UserForm handleCancel={handleCancel} handleSubmit={handleSubmit} />
        </CardBody>
        {formSubmitError ? (
          <div className="formSubmitError">formSubmitError</div>
        ) : (
          ''
        )}
      </Card>
    </PageSection>
  );
}

export default UserAdd;
