import React, { useState, useEffect } from 'react';
import { useHistory } from 'react-router-dom';
import { object } from 'prop-types';

import { CardBody } from '@components/Card';
import { CredentialsAPI, CredentialTypesAPI } from '@api';
import ContentError from '@components/ContentError';
import ContentLoading from '@components/ContentLoading';
import CredentialForm from '../shared/CredentialForm';

function CredentialEdit({ credential, me }) {
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
    const url = `/credentials/${credential.id}/details`;

    history.push(`${url}`);
  };

  const handleSubmit = async values => {
    const { organization, ...remainingValues } = values;
    setFormSubmitError(null);
    try {
      const {
        data: { id: credentialId },
      } = await CredentialsAPI.update(credential.id, {
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
    return <ContentError />;
  }

  if (isLoading) {
    return <ContentLoading />;
  }

  return (
    <CardBody>
      <CredentialForm
        onCancel={handleCancel}
        onSubmit={handleSubmit}
        credential={credential}
        credentialTypes={credentialTypes}
        submitError={formSubmitError}
      />
    </CardBody>
  );
}

CredentialEdit.proptype = {
  inventory: object.isRequired,
};

export { CredentialEdit as _CredentialEdit };
export default CredentialEdit;
