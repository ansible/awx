import React, { useState, useEffect } from 'react';
import { useHistory } from 'react-router-dom';
import { PageSection, Card } from '@patternfly/react-core';
import { CardBody } from '@components/Card';
import ContentError from '@components/ContentError';
import ContentLoading from '@components/ContentLoading';

import { CredentialTypesAPI, CredentialsAPI } from '@api';
import CredentialForm from '../shared/CredentialForm';

function CredentialAdd({ me }) {
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [credentialTypes, setCredentialTypes] = useState(null);
  const [formSubmitError, setFormSubmitError] = useState(null);
  const history = useHistory();

  useEffect(() => {
    const loadData = async () => {
      try {
        const {
          data: { results: loadedCredentialTypes },
        } = await CredentialTypesAPI.read({ or__kind: ['scm', 'ssh'] });
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
    const { organization, ...remainingValues } = values;
    setFormSubmitError(null);
    try {
      const {
        data: { id: credentialId },
      } = await CredentialsAPI.create({
        user: (me && me.id) || null,
        organization: (organization && organization.id) || null,
        ...remainingValues,
      });
      const url = `/credentials/${credentialId}/details`;
      history.push(`${url}`);
    } catch (err) {
      setFormSubmitError(err);
    }
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
    return <ContentLoading />;
  }
  return (
    <PageSection>
      <Card>
        <CardBody>
          <CredentialForm
            onCancel={handleCancel}
            onSubmit={handleSubmit}
            credentialTypes={credentialTypes}
            submitError={formSubmitError}
          />
        </CardBody>
      </Card>
    </PageSection>
  );
}

export { CredentialAdd as _CredentialAdd };
export default CredentialAdd;
