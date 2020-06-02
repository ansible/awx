import React, { useCallback, useState, useEffect } from 'react';
import { useHistory } from 'react-router-dom';
import { PageSection, Card } from '@patternfly/react-core';
import { CardBody } from '../../../components/Card';
import ContentError from '../../../components/ContentError';
import ContentLoading from '../../../components/ContentLoading';

import {
  CredentialInputSourcesAPI,
  CredentialTypesAPI,
  CredentialsAPI,
} from '../../../api';
import CredentialForm from '../shared/CredentialForm';
import useRequest from '../../../util/useRequest';

function CredentialAdd({ me }) {
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [credentialTypes, setCredentialTypes] = useState(null);
  const history = useHistory();

  const {
    error: submitError,
    request: submitRequest,
    result: credentialId,
  } = useRequest(
    useCallback(
      async values => {
        const { inputs, organization, ...remainingValues } = values;
        const nonPluginInputs = {};
        const pluginInputs = {};
        Object.entries(inputs).forEach(([key, value]) => {
          if (value.credential && value.inputs) {
            pluginInputs[key] = value;
          } else {
            nonPluginInputs[key] = value;
          }
        });
        const {
          data: { id: newCredentialId },
        } = await CredentialsAPI.create({
          user: (me && me.id) || null,
          organization: (organization && organization.id) || null,
          inputs: nonPluginInputs,
          ...remainingValues,
        });
        const inputSourceRequests = [];
        Object.entries(pluginInputs).forEach(([key, value]) => {
          inputSourceRequests.push(
            CredentialInputSourcesAPI.create({
              input_field_name: key,
              metadata: value.inputs,
              source_credential: value.credential.id,
              target_credential: newCredentialId,
            })
          );
        });
        await Promise.all(inputSourceRequests);

        return newCredentialId;
      },
      [me]
    )
  );

  useEffect(() => {
    if (credentialId) {
      history.push(`/credentials/${credentialId}/details`);
    }
  }, [credentialId, history]);

  useEffect(() => {
    const loadData = async () => {
      try {
        const {
          data: { results: loadedCredentialTypes },
        } = await CredentialTypesAPI.read({
          or__namespace: ['gce', 'scm', 'ssh'],
        });
        setCredentialTypes(loadedCredentialTypes);
      } catch (err) {
        setError(err);
      } finally {
        setIsLoading(false);
      }
    };
    loadData();
  }, []);

  const handleCancel = () => {
    history.push('/credentials');
  };

  const handleSubmit = async values => {
    await submitRequest(values);
  };

  if (error) {
    return (
      <PageSection>
        <Card>
          <CardBody>
            <ContentError error={error} />
          </CardBody>
        </Card>
      </PageSection>
    );
  }
  if (isLoading) {
    return (
      <PageSection>
        <Card>
          <CardBody>
            <ContentLoading />
          </CardBody>
        </Card>
      </PageSection>
    );
  }
  return (
    <PageSection>
      <Card>
        <CardBody>
          <CredentialForm
            onCancel={handleCancel}
            onSubmit={handleSubmit}
            credentialTypes={credentialTypes}
            submitError={submitError}
          />
        </CardBody>
      </Card>
    </PageSection>
  );
}

export { CredentialAdd as _CredentialAdd };
export default CredentialAdd;
