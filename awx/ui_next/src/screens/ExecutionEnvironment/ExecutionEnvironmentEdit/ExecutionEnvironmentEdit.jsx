import React, { useState } from 'react';
import { useHistory } from 'react-router-dom';

import { CardBody } from '../../../components/Card';
import { ExecutionEnvironmentsAPI } from '../../../api';
import ExecutionEnvironmentForm from '../shared/ExecutionEnvironmentForm';
import { Config } from '../../../contexts/Config';

function ExecutionEnvironmentEdit({ executionEnvironment }) {
  const history = useHistory();
  const [submitError, setSubmitError] = useState(null);
  const detailsUrl = `/execution_environments/${executionEnvironment.id}/details`;

  const handleSubmit = async values => {
    try {
      await ExecutionEnvironmentsAPI.update(executionEnvironment.id, {
        ...values,
        credential: values.credential ? values.credential.id : null,
        organization: values.organization ? values.organization.id : null,
      });
      history.push(detailsUrl);
    } catch (error) {
      setSubmitError(error);
    }
  };

  const handleCancel = () => {
    history.push(detailsUrl);
  };
  return (
    <CardBody>
      <Config>
        {({ me }) => (
          <ExecutionEnvironmentForm
            executionEnvironment={executionEnvironment}
            onSubmit={handleSubmit}
            submitError={submitError}
            onCancel={handleCancel}
            me={me || {}}
          />
        )}
      </Config>
    </CardBody>
  );
}

export default ExecutionEnvironmentEdit;
