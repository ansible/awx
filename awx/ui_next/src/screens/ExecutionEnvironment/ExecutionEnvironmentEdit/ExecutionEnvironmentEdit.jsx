import React, { useState } from 'react';
import { useHistory } from 'react-router-dom';

import { CardBody } from '../../../components/Card';
import { ExecutionEnvironmentsAPI } from '../../../api';
import ExecutionEnvironmentForm from '../shared/ExecutionEnvironmentForm';

function ExecutionEnvironmentEdit({ executionEnvironment }) {
  const history = useHistory();
  const [submitError, setSubmitError] = useState(null);
  const detailsUrl = `/execution_environments/${executionEnvironment.id}/details`;

  const handleSubmit = async values => {
    try {
      await ExecutionEnvironmentsAPI.update(executionEnvironment.id, {
        ...values,
        credential: values.credential ? values.credential.id : null,
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
      <ExecutionEnvironmentForm
        executionEnvironment={executionEnvironment}
        onSubmit={handleSubmit}
        submitError={submitError}
        onCancel={handleCancel}
      />
    </CardBody>
  );
}

export default ExecutionEnvironmentEdit;
