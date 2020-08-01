import React, { useCallback, useEffect, useState } from 'react';
import { useHistory } from 'react-router-dom';

import { Card, PageSection } from '@patternfly/react-core';
import useRequest from '../../../util/useRequest';
import ContentError from '../../../components/ContentError';
import ApplicationForm from '../shared/ApplicationForm';
import { ApplicationsAPI } from '../../../api';
import { CardBody } from '../../../components/Card';

function ApplicationAdd() {
  const history = useHistory();
  const [submitError, setSubmitError] = useState(null);

  const {
    error,
    request: fetchOptions,
    result: { authorizationOptions, clientTypeOptions },
  } = useRequest(
    useCallback(async () => {
      const {
        data: {
          actions: {
            GET: {
              authorization_grant_type: { choices: authChoices },
              client_type: { choices: clientChoices },
            },
          },
        },
      } = await ApplicationsAPI.readOptions();

      const authorization = authChoices.map(choice => ({
        value: choice[0],
        label: choice[1],
        key: choice[0],
      }));
      const clientType = clientChoices.map(choice => ({
        value: choice[0],
        label: choice[1],
        key: choice[0],
      }));

      return {
        authorizationOptions: authorization,
        clientTypeOptions: clientType,
      };
    }, []),
    {
      authorizationOptions: [],
      clientTypeOptions: [],
    }
  );
  const handleSubmit = async ({ ...values }) => {
    values.organization = values.organization.id;
    try {
      const {
        data: { id },
      } = await ApplicationsAPI.create(values);
      history.push(`/applications/${id}/details`);
    } catch (err) {
      setSubmitError(err);
    }
  };

  const handleCancel = () => {
    history.push(`/applications`);
  };

  useEffect(() => {
    fetchOptions();
  }, [fetchOptions]);

  if (error) {
    return <ContentError error={error} />;
  }
  return (
    <>
      <PageSection>
        <Card>
          <CardBody>
            <ApplicationForm
              onSubmit={handleSubmit}
              onCancel={handleCancel}
              authorizationOptions={authorizationOptions}
              clientTypeOptions={clientTypeOptions}
              submitError={submitError}
            />
          </CardBody>
        </Card>
      </PageSection>
    </>
  );
}
export default ApplicationAdd;
