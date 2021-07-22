import React, { useState } from 'react';
import { useHistory } from 'react-router-dom';

import { CardBody } from 'components/Card';
import { UsersAPI } from 'api';
import UserForm from '../shared/UserForm';

function UserEdit({ user }) {
  const [formSubmitError, setFormSubmitError] = useState(null);

  const history = useHistory();

  const handleSubmit = async (values) => {
    setFormSubmitError(null);
    try {
      delete values.organization;
      await UsersAPI.update(user.id, values);
      history.push(`/users/${user.id}/details`);
    } catch (error) {
      setFormSubmitError(error);
    }
  };

  const handleCancel = () => {
    history.push(`/users/${user.id}/details`);
  };

  return (
    <CardBody>
      <UserForm
        user={user}
        handleCancel={handleCancel}
        handleSubmit={handleSubmit}
        submitError={formSubmitError}
      />
    </CardBody>
  );
}

export default UserEdit;
