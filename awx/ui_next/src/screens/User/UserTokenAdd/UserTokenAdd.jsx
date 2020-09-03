import React, { useCallback } from 'react';
import { useHistory, useParams } from 'react-router-dom';

import { CardBody } from '../../../components/Card';
import { TokensAPI, UsersAPI } from '../../../api';
import useRequest from '../../../util/useRequest';
import UserTokenFrom from '../shared/UserTokenForm';

function UserTokenAdd() {
  const history = useHistory();
  const { id: userId } = useParams();
  const { error: submitError, request: handleSubmit } = useRequest(
    useCallback(
      async formData => {
        if (formData.application) {
          formData.application = formData.application?.id || null;
          await UsersAPI.createToken(userId, formData);
        } else {
          await TokensAPI.create(formData);
        }

        history.push(`/users/${userId}/tokens`);
      },
      [history, userId]
    )
  );

  const handleCancel = () => {
    history.push(`/users/${userId}/tokens`);
  };

  return (
    <CardBody>
      <UserTokenFrom
        handleCancel={handleCancel}
        handleSubmit={handleSubmit}
        submitError={submitError}
      />
    </CardBody>
  );
}
export default UserTokenAdd;
