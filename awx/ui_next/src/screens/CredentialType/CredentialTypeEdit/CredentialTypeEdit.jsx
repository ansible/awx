import React, { useState } from 'react';
import { useHistory } from 'react-router-dom';

import { CardBody } from '../../../components/Card';
import { CredentialTypesAPI } from '../../../api';
import CredentialTypeForm from '../shared/CredentialTypeForm';
import { parseVariableField } from '../../../util/yaml';

function CredentialTypeEdit({ credentialType }) {
  const history = useHistory();
  const [submitError, setSubmitError] = useState(null);
  const detailsUrl = `/credential_types/${credentialType.id}/details`;

  const handleSubmit = async values => {
    try {
      await CredentialTypesAPI.update(credentialType.id, {
        ...values,
        injectors: parseVariableField(values.injectors),
        inputs: parseVariableField(values.inputs),
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
      <CredentialTypeForm
        credentialType={credentialType}
        onSubmit={handleSubmit}
        submitError={submitError}
        onCancel={handleCancel}
      />
    </CardBody>
  );
}

export default CredentialTypeEdit;
