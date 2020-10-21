import React, { Fragment, useEffect, useCallback } from 'react';
import { Link, useHistory } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { shape } from 'prop-types';
import styled from 'styled-components';
import { Button, List, ListItem } from '@patternfly/react-core';
import AlertModal from '../../../components/AlertModal';
import { CardBody, CardActionsRow } from '../../../components/Card';
import ContentError from '../../../components/ContentError';
import ContentLoading from '../../../components/ContentLoading';
import DeleteButton from '../../../components/DeleteButton';
import {
  Detail,
  DetailList,
  UserDateDetail,
} from '../../../components/DetailList';
import ChipGroup from '../../../components/ChipGroup';
import CodeMirrorInput from '../../../components/CodeMirrorInput';
import CredentialChip from '../../../components/CredentialChip';
import ErrorDetail from '../../../components/ErrorDetail';
import { CredentialsAPI, CredentialTypesAPI } from '../../../api';
import { Credential } from '../../../types';
import useRequest, { useDismissableError } from '../../../util/useRequest';

const PluginInputMetadata = styled(CodeMirrorInput)`
  grid-column: 1 / -1;
`;

const PluginFieldText = styled.p`
  margin-top: 10px;
`;

function CredentialDetail({ i18n, credential }) {
  const {
    id: credentialId,
    name,
    description,
    inputs,
    created,
    modified,
    summary_fields: {
      credential_type,
      organization,
      created_by,
      modified_by,
      user_capabilities,
    },
  } = credential;
  const history = useHistory();

  const {
    result: { fields, managedByTower, inputSources },
    request: fetchDetails,
    isLoading: hasContentLoading,
    error: contentError,
  } = useRequest(
    useCallback(async () => {
      const [
        {
          data: { inputs: credentialTypeInputs, managed_by_tower },
        },
        {
          data: { results: loadedInputSources },
        },
      ] = await Promise.all([
        CredentialTypesAPI.readDetail(credential_type.id),
        CredentialsAPI.readInputSources(credentialId),
      ]);
      return {
        fields: credentialTypeInputs.fields || [],
        managedByTower: managed_by_tower,
        inputSources: loadedInputSources.reduce(
          (inputSourcesMap, inputSource) => {
            inputSourcesMap[inputSource.input_field_name] = inputSource;
            return inputSourcesMap;
          },
          {}
        ),
      };
    }, [credentialId, credential_type]),
    {
      fields: [],
      managedByTower: true,
      inputSources: {},
    }
  );

  const {
    request: deleteCredential,
    isLoading,
    error: deleteError,
  } = useRequest(
    useCallback(async () => {
      await CredentialsAPI.destroy(credentialId);
      history.push('/credentials');
    }, [credentialId, history])
  );

  const { error, dismissError } = useDismissableError(deleteError);

  const renderDetail = ({ id, label, type, ask_at_runtime }) => {
    if (inputSources[id]) {
      return (
        <Fragment key={id}>
          <Detail
            id={`credential-${id}-detail`}
            fullWidth
            label={<span>{label} *</span>}
            value={
              <ChipGroup numChips={1} totalChips={1}>
                <CredentialChip
                  credential={inputSources[id].summary_fields.source_credential}
                  isReadOnly
                />
              </ChipGroup>
            }
          />
          <PluginInputMetadata
            id={`credential-${id}-metadata`}
            mode="javascript"
            readOnly
            value={JSON.stringify(inputSources[id].metadata, null, 2)}
            onChange={() => {}}
            rows={5}
            hasErrors={false}
          />
        </Fragment>
      );
    }

    if (type === 'boolean') {
      return (
        <Detail
          id={`credential-${id}-detail`}
          key={id}
          label={i18n._(t`Options`)}
          value={<List>{inputs[id] && <ListItem>{label}</ListItem>}</List>}
        />
      );
    }

    if (inputs[id] === '$encrypted$') {
      return (
        <Detail
          id={`credential-${id}-detail`}
          key={id}
          label={label}
          value={i18n._(t`Encrypted`)}
          isEncrypted
        />
      );
    }

    if (ask_at_runtime && inputs[id] === 'ASK') {
      return (
        <Detail
          id={`credential-${id}-detail`}
          key={id}
          label={label}
          value={i18n._(t`Prompt on launch`)}
        />
      );
    }

    return (
      <Detail
        id={`credential-${id}-detail`}
        key={id}
        label={label}
        value={inputs[id]}
      />
    );
  };

  useEffect(() => {
    fetchDetails();
  }, [fetchDetails]);

  if (hasContentLoading) {
    return <ContentLoading />;
  }

  if (contentError) {
    return <ContentError error={contentError} />;
  }

  return (
    <CardBody>
      <DetailList>
        <Detail
          id="credential-name-detail"
          label={i18n._(t`Name`)}
          value={name}
        />
        <Detail
          id="credential-description-detail"
          label={i18n._(t`Description`)}
          value={description}
        />
        {organization && (
          <Detail
            id="credential-organization-detail"
            label={i18n._(t`Organization`)}
            value={
              <Link to={`/organizations/${organization.id}/details`}>
                {organization.name}
              </Link>
            }
          />
        )}
        <Detail
          id="credential-credential_type-detail"
          label={i18n._(t`Credential Type`)}
          value={
            managedByTower ? (
              credential_type.name
            ) : (
              <Link to={`/credential_types/${credential_type.id}/details`}>
                {credential_type.name}
              </Link>
            )
          }
        />

        {fields.map(field => renderDetail(field))}

        <UserDateDetail
          id="credential-created-detail"
          label={i18n._(t`Created`)}
          date={created}
          user={created_by}
        />
        <UserDateDetail
          id="credential-last_modified-detail"
          label={i18n._(t`Last Modified`)}
          date={modified}
          user={modified_by}
        />
      </DetailList>
      {Object.keys(inputSources).length > 0 && (
        <PluginFieldText>
          {i18n._(
            t`* This field will be retrieved from an external secret management system using the specified credential.`
          )}
        </PluginFieldText>
      )}
      <CardActionsRow>
        {user_capabilities.edit && (
          <Button component={Link} to={`/credentials/${credentialId}/edit`}>
            {i18n._(t`Edit`)}
          </Button>
        )}
        {user_capabilities.delete && (
          <DeleteButton
            name={name}
            modalTitle={i18n._(t`Delete Credential`)}
            onConfirm={deleteCredential}
            isLoading={isLoading}
          >
            {i18n._(t`Delete`)}
          </DeleteButton>
        )}
      </CardActionsRow>
      {error && (
        <AlertModal
          isOpen={error}
          variant="error"
          title={i18n._(t`Error!`)}
          onClose={dismissError}
        >
          {i18n._(t`Failed to delete credential.`)}
          <ErrorDetail error={error} />
        </AlertModal>
      )}
    </CardBody>
  );
}

CredentialDetail.propTypes = {
  credential: Credential.isRequired,
  i18n: shape({}).isRequired,
};

export default withI18n()(CredentialDetail);
