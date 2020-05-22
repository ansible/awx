import React, { useState, useEffect } from 'react';
import { useHistory } from 'react-router-dom';
import { object } from 'prop-types';

import { CardBody } from '../../../components/Card';
import {
  CredentialsAPI,
  CredentialInputSourcesAPI,
  CredentialTypesAPI,
} from '../../../api';
import ContentError from '../../../components/ContentError';
import ContentLoading from '../../../components/ContentLoading';
import CredentialForm from '../shared/CredentialForm';

function CredentialEdit({ credential, me }) {
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [credentialTypes, setCredentialTypes] = useState(null);
  const [inputSources, setInputSources] = useState(null);
  const [formSubmitError, setFormSubmitError] = useState(null);
  const history = useHistory();

  useEffect(() => {
    const loadData = async () => {
      try {
        const [
          {
            data: { results: loadedCredentialTypes },
          },
          {
            data: { results: loadedInputSources },
          },
        ] = await Promise.all([
          CredentialTypesAPI.read({
            or__namespace: ['gce', 'scm', 'ssh'],
          }),
          CredentialsAPI.readInputSources(credential.id, { page_size: 200 }),
        ]);
        setCredentialTypes(loadedCredentialTypes);
        const inputSourcesMap = {};
        loadedInputSources.forEach(inputSource => {
          inputSourcesMap[inputSource.input_field_name] = inputSource;
        });
        setInputSources(inputSourcesMap);
      } catch (err) {
        setError(err);
      } finally {
        setIsLoading(false);
      }
    };
    loadData();
  }, [credential.id]);

  const handleCancel = () => {
    const url = `/credentials/${credential.id}/details`;

    history.push(`${url}`);
  };

  const createAndUpdateInputSources = pluginInputs =>
    Object.entries(pluginInputs).map(([fieldName, fieldValue]) => {
      if (!inputSources[fieldName]) {
        return CredentialInputSourcesAPI.create({
          input_field_name: fieldName,
          metadata: fieldValue.inputs,
          source_credential: fieldValue.credential.id,
          target_credential: credential.id,
        });
      }
      if (fieldValue.touched) {
        return CredentialInputSourcesAPI.update(inputSources[fieldName].id, {
          metadata: fieldValue.inputs,
          source_credential: fieldValue.credential.id,
        });
      }

      return null;
    });

  const destroyInputSources = inputs => {
    const destroyRequests = [];
    Object.values(inputSources).forEach(inputSource => {
      const { id, input_field_name } = inputSource;
      if (!inputs[input_field_name]?.credential) {
        destroyRequests.push(CredentialInputSourcesAPI.destroy(id));
      }
    });
    return destroyRequests;
  };

  const handleSubmit = async values => {
    const { inputs, organization, ...remainingValues } = values;
    const pluginInputs = {};
    Object.entries(inputs).forEach(([key, value]) => {
      if (value.credential && value.inputs) {
        pluginInputs[key] = value;
        delete inputs[key];
      }
    });
    setFormSubmitError(null);
    try {
      await Promise.all([
        CredentialsAPI.update(credential.id, {
          user: (me && me.id) || null,
          organization: (organization && organization.id) || null,
          inputs: inputs || {},
          ...remainingValues,
        }),
        ...destroyInputSources(pluginInputs),
      ]);
      await Promise.all(createAndUpdateInputSources(pluginInputs));
      const url = `/credentials/${credential.id}/details`;
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
        inputSources={inputSources}
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
