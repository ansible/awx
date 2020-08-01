import React, { useState } from 'react';
import { useHistory } from 'react-router-dom';
import { PageSection, Card } from '@patternfly/react-core';

import HostForm from '../../../components/HostForm';
import { CardBody } from '../../../components/Card';
import { HostsAPI } from '../../../api';

function HostAdd() {
  const [formError, setFormError] = useState(null);
  const history = useHistory();

  const handleSubmit = async formData => {
    try {
      const { data: response } = await HostsAPI.create(formData);
      history.push(`/hosts/${response.id}/details`);
    } catch (error) {
      setFormError(error);
    }
  };

  const handleCancel = () => {
    history.push(`/hosts`);
  };

  return (
    <PageSection>
      <Card>
        <CardBody>
          <HostForm
            handleSubmit={handleSubmit}
            handleCancel={handleCancel}
            submitError={formError}
          />
        </CardBody>
      </Card>
    </PageSection>
  );
}

export default HostAdd;
