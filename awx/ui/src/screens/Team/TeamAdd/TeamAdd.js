import React, { useState } from 'react';
import { useHistory } from 'react-router-dom';
import { PageSection, Card } from '@patternfly/react-core';

import { TeamsAPI } from 'api';
import { Config } from 'contexts/Config';
import { CardBody } from 'components/Card';
import TeamForm from '../shared/TeamForm';

function TeamAdd() {
  const [submitError, setSubmitError] = useState(null);
  const history = useHistory();

  const handleSubmit = async (values) => {
    try {
      const {
        name,
        description,
        organization: { id },
      } = values;
      const valuesToSend = { name, description, organization: id };
      const { data: response } = await TeamsAPI.create(valuesToSend);
      history.push(`/teams/${response.id}`);
    } catch (error) {
      setSubmitError(error);
    }
  };

  const handleCancel = () => {
    history.push('/teams');
  };

  return (
    <PageSection>
      <Card>
        <CardBody>
          <Config>
            {({ me }) => (
              <TeamForm
                handleSubmit={handleSubmit}
                handleCancel={handleCancel}
                me={me || {}}
                submitError={submitError}
              />
            )}
          </Config>
        </CardBody>
      </Card>
    </PageSection>
  );
}

export { TeamAdd as _TeamAdd };
export default TeamAdd;
