import React, { useState } from 'react';
import { withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { CardBody } from '@patternfly/react-core';
import UserForm from '../shared/UserForm';
import { UsersAPI } from '@api';

function UserEdit({ user, history }) {
  const [formSubmitError, setFormSubmitError] = useState(null);

  const handleSubmit = async values => {
    try {
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
      />
      {formSubmitError ? <div> error </div> : null}
    </CardBody>
  );
}

export default withI18n()(withRouter(UserEdit));
