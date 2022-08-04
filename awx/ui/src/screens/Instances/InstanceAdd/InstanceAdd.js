import React, { useState } from 'react';
import { useHistory } from 'react-router-dom';
import { Card, PageSection } from '@patternfly/react-core';
import { InstancesAPI } from 'api';
import InstanceForm from '../Shared/InstanceForm';

function InstanceAdd() {
  const history = useHistory();
  const [formError, setFormError] = useState();
  const handleSubmit = async (values) => {
    try {
      const {
        data: { id },
      } = await InstancesAPI.create(values);

      history.push(`/instances/${id}/details`);
    } catch (err) {
      setFormError(err);
    }
  };

  const handleCancel = () => {
    history.push('/instances');
  };

  return (
    <PageSection>
      <Card>
        <InstanceForm
          submitError={formError}
          handleSubmit={handleSubmit}
          handleCancel={handleCancel}
        />
      </Card>
    </PageSection>
  );
}

export default InstanceAdd;
