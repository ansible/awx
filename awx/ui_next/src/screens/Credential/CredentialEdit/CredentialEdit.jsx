import React, { useCallback, useState, useEffect } from 'react';
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
import useRequest from '../../../util/useRequest';

function CredentialEdit({ credential, me }) {
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [credentialTypes, setCredentialTypes] = useState(null);
  const [inputSources, setInputSources] = useState({});
  const history = useHistory();

  const { error: submitError, request: submitRequest, result } = useRequest(
    useCallback(
      async (values, inputSourceMap) => {
        const createAndUpdateInputSources = pluginInputs =>
          Object.entries(pluginInputs).map(([fieldName, fieldValue]) => {
            if (!inputSourceMap[fieldName]) {
              return CredentialInputSourcesAPI.create({
                input_field_name: fieldName,
                metadata: fieldValue.inputs,
                source_credential: fieldValue.credential.id,
                target_credential: credential.id,
              });
            }
            if (fieldValue.touched) {
              return CredentialInputSourcesAPI.update(
                inputSourceMap[fieldName].id,
                {
                  metadata: fieldValue.inputs,
                  source_credential: fieldValue.credential.id,
                }
              );
            }

            return null;
          });

        const destroyInputSources = inputs => {
          const destroyRequests = [];
          Object.values(inputSourceMap).forEach(inputSource => {
            const { id, input_field_name } = inputSource;
            if (!inputs[input_field_name]?.credential) {
              destroyRequests.push(CredentialInputSourcesAPI.destroy(id));
            }
          });
          return destroyRequests;
        };

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
        const [{ data }] = await Promise.all([
          CredentialsAPI.update(credential.id, {
            user: (me && me.id) || null,
            organization: (organization && organization.id) || null,
            inputs: nonPluginInputs,
            ...remainingValues,
          }),
          ...destroyInputSources(inputs),
        ]);
        await Promise.all(createAndUpdateInputSources(pluginInputs));
        return data;
      },
      [credential.id, me]
    )
  );

  useEffect(() => {
    if (result) {
      history.push(`/credentials/${result.id}/details`);
    }
  }, [result, history]);

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
        setInputSources(
          loadedInputSources.reduce((inputSourcesMap, inputSource) => {
            inputSourcesMap[inputSource.input_field_name] = inputSource;
            return inputSourcesMap;
          }, {})
        );
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

  const handleSubmit = async values => {
    await submitRequest(values, inputSources);
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
        submitError={submitError}
      />
    </CardBody>
  );
}

CredentialEdit.proptype = {
  inventory: object.isRequired,
};

export { CredentialEdit as _CredentialEdit };
export default CredentialEdit;
