import React, { useState } from 'react';
import { Card, PageSection } from '@patternfly/react-core';
import { useHistory } from 'react-router-dom';

import ExecutionEnvironmentForm from '../shared/ExecutionEnvironmentForm';
import { CardBody } from '../../../components/Card';
import { ExecutionEnvironmentsAPI } from '../../../api';

function ExecutionEnvironmentAdd() {
  const history = useHistory();
  const [submitError, setSubmitError] = useState(null);

  const handleSubmit = async values => {
    try {
      const { data: response } = await ExecutionEnvironmentsAPI.create({
        ...values,
        credential: values?.credential?.id,
      });
      history.push(`/execution_environments/${response.id}/details`);
    } catch (error) {
      setSubmitError(error);
    }
  };

  const handleCancel = () => {
    history.push(`/execution_environments`);
  };
  return (
    <PageSection>
      <Card>
        <CardBody>
          <ExecutionEnvironmentForm
            onSubmit={handleSubmit}
            submitError={submitError}
            onCancel={handleCancel}
          />
        </CardBody>
      </Card>
    </PageSection>
  );
}

export default ExecutionEnvironmentAdd;
