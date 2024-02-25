import React, { useCallback, useEffect, useState } from 'react';
import { useHistory, useParams } from 'react-router-dom';
import { CardBody } from 'components/Card';
import {
  CredentialsAPI,
  CredentialInputSourcesAPI,
  CredentialTypesAPI,
  OrganizationsAPI,
  UsersAPI,
} from 'api';
import ContentError from 'components/ContentError';
import ContentLoading from 'components/ContentLoading';
import useRequest from 'hooks/useRequest';
import { useConfig } from 'contexts/Config';
import { Credential } from 'types';
import CredentialForm from '../shared/CredentialForm';

function CredentialEdit({ credential }) {
  const history = useHistory();
  const { id: credId } = useParams();
  const { me = {} } = useConfig();
  const [isOrgLookupDisabled, setIsOrgLookupDisabled] = useState(false);

  const {
    error: submitError,
    request: submitRequest,
    result,
  } = useRequest(
    useCallback(
      async (values, credentialTypesMap, inputSourceMap) => {
        const { inputs: credentialTypeInputs } =
          credentialTypesMap[values.credential_type];

        const { inputs, organization, passwordPrompts, ...remainingValues } =
          values;

        const nonPluginInputs = {};
        const pluginInputs = {};
        const possibleFields = credentialTypeInputs.fields || [];

        possibleFields.forEach((field) => {
          const input = inputs[field.id];
          if (input?.credential && input?.inputs) {
            pluginInputs[field.id] = input;
          } else if (passwordPrompts[field.id]) {
            nonPluginInputs[field.id] = 'ASK';
          } else {
            nonPluginInputs[field.id] = input;
          }
        });

        const createAndUpdateInputSources = () =>
          Object.entries(pluginInputs).map(([fieldName, fieldValue]) => {
            if (!inputSourceMap[fieldName]) {
              return CredentialInputSourcesAPI.create({
                input_field_name: fieldName,
                metadata: fieldValue.inputs,
                source_credential: fieldValue.credential.id,
                target_credential: credId,
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

        const destroyInputSources = () =>
          Object.values(inputSourceMap).map((inputSource) => {
            const { id, input_field_name } = inputSource;
            if (!inputs[input_field_name]?.credential) {
              return CredentialInputSourcesAPI.destroy(id);
            }
            return null;
          });

        const modifiedData = { inputs: nonPluginInputs, ...remainingValues };
        // can send only one of org, user, team
        if (organization?.id) {
          modifiedData.organization = organization.id;
        } else {
          modifiedData.organization = null;
          if (me?.id) {
            modifiedData.user = me.id;
          }
        }

        if (credential.kind === 'vault' && !credential.inputs?.vault_id) {
          delete modifiedData.inputs.vault_id;
        }

        const [{ data }] = await Promise.all([
          CredentialsAPI.update(credId, modifiedData),
          ...destroyInputSources(),
        ]);

        await Promise.all(createAndUpdateInputSources());

        return data;
      },
      [me, credId, credential]
    )
  );

  useEffect(() => {
    if (result) {
      history.push(`/credentials/${result.id}/details`);
    }
  }, [result, history]);
  const {
    isLoading,
    error,
    request: loadData,
    result: { credentialTypes, loadedInputSources },
  } = useRequest(
    useCallback(async () => {
      const [
        { data },
        {
          data: { results },
        },
        {
          data: { count: adminOrgCount },
        },
        {
          data: { count: credentialAdminCount },
        },
      ] = await Promise.all([
        CredentialTypesAPI.read({ page_size: 200 }),
        CredentialsAPI.readInputSources(credId),
        UsersAPI.readAdminOfOrganizations(me.id),
        OrganizationsAPI.read({
          page_size: 1,
          role_level: 'credential_admin_role',
        }),
      ]);
      setIsOrgLookupDisabled(!(adminOrgCount || credentialAdminCount));
      const credTypes = data.results;
      if (data.next && data.next.includes('page=2')) {
        const {
          data: { results: additionalCredTypes },
        } = await CredentialTypesAPI.read({
          page_size: 200,
          page: 2,
        });
        credTypes.concat([...additionalCredTypes]);
      }
      const creds = credTypes.reduce((credentialTypesMap, credentialType) => {
        credentialTypesMap[credentialType.id] = credentialType;
        return credentialTypesMap;
      }, {});
      const inputSources = results.reduce((inputSourcesMap, inputSource) => {
        inputSourcesMap[inputSource.input_field_name] = inputSource;
        return inputSourcesMap;
      }, {});
      return { credentialTypes: creds, loadedInputSources: inputSources };
    }, [credId, me.id]),
    {}
  );

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleCancel = () => {
    const url = `/credentials/${credId}/details`;
    history.push(`${url}`);
  };

  const handleSubmit = async (values) => {
    await submitRequest(values, credentialTypes, loadedInputSources);
  };

  if (error) {
    return <ContentError error={error} />;
  }

  if (isLoading || !credentialTypes) {
    return <ContentLoading />;
  }

  return (
    <CardBody>
      <CredentialForm
        onCancel={handleCancel}
        onSubmit={handleSubmit}
        credential={credential}
        credentialTypes={credentialTypes}
        inputSources={loadedInputSources}
        submitError={submitError}
        isOrgLookupDisabled={isOrgLookupDisabled}
      />
    </CardBody>
  );
}

CredentialEdit.propTypes = {
  credential: Credential.isRequired,
};

export { CredentialEdit as _CredentialEdit };
export default CredentialEdit;
