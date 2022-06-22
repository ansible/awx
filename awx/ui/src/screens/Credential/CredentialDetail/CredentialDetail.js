import React, { useEffect, useCallback } from 'react';
import { Link, useHistory } from 'react-router-dom';
import { t } from '@lingui/macro';
import styled from 'styled-components';
import {
  Button,
  TextList,
  TextListItem,
  TextListVariants,
  TextListItemVariants,
} from '@patternfly/react-core';
import AlertModal from 'components/AlertModal';
import { CardBody, CardActionsRow } from 'components/Card';
import ContentError from 'components/ContentError';
import ContentLoading from 'components/ContentLoading';
import DeleteButton from 'components/DeleteButton';
import { Detail, DetailList, UserDateDetail } from 'components/DetailList';
import ChipGroup from 'components/ChipGroup';
import CodeEditor from 'components/CodeEditor';
import CredentialChip from 'components/CredentialChip';
import ErrorDetail from 'components/ErrorDetail';
import { CredentialsAPI, CredentialTypesAPI } from 'api';
import { Credential } from 'types';
import useRequest, { useDismissableError } from 'hooks/useRequest';
import { relatedResourceDeleteRequests } from 'util/getRelatedResourceDeleteDetails';

const PluginInputMetadata = styled.div`
  grid-column: 1 / -1;
`;

const PluginFieldText = styled.p`
  margin-top: 10px;
`;

function CredentialDetail({ credential }) {
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
          data: { inputs: credentialTypeInputs, managed },
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
        managedByTower: managed,
        inputSources: loadedInputSources.reduce(
          (inputSourcesMap, inputSource) => {
            inputSourcesMap[inputSource.input_field_name] = inputSource;
            return inputSourcesMap;
          },
          {}
        ),
      };
    }, [credentialId, credential_type.id]),
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

  const renderDetail = ({
    id,
    label,
    type,
    ask_at_runtime,
    help_text = '',
  }) => {
    if (inputSources[id]) {
      return (
        <React.Fragment key={id}>
          <Detail
            dataCy={`credential-${id}-detail`}
            helpText={help_text}
            id={`credential-${id}-detail`}
            fullWidth
            label={<span>{label} *</span>}
            value={
              <ChipGroup
                numChips={1}
                totalChips={1}
                ouiaId={`credential-${id}-chips`}
              >
                <CredentialChip
                  credential={inputSources[id].summary_fields.source_credential}
                  ouiaId={`credential-${id}-chip`}
                  isReadOnly
                />
              </ChipGroup>
            }
          />
          <PluginInputMetadata>
            <CodeEditor
              dataCy={`credential-${id}-detail`}
              id={`credential-${id}-metadata`}
              mode="javascript"
              readOnly
              value={JSON.stringify(inputSources[id].metadata, null, 2)}
              onChange={() => {}}
              rows={5}
              hasErrors={false}
            />
          </PluginInputMetadata>
        </React.Fragment>
      );
    }

    if (type === 'boolean') {
      return null;
    }

    if (inputs[id] === '$encrypted$') {
      return (
        <Detail
          dataCy={`credential-${id}-detail`}
          id={`credential-${id}-detail`}
          key={id}
          label={label}
          value={t`Encrypted`}
          helpText={help_text}
          isEncrypted
        />
      );
    }

    if (ask_at_runtime && inputs[id] === 'ASK') {
      return (
        <Detail
          dataCy={`credential-${id}-detail`}
          helpText={help_text}
          id={`credential-${id}-detail`}
          key={id}
          label={label}
          value={t`Prompt on launch`}
        />
      );
    }

    return (
      <Detail
        dataCy={`credential-${id}-detail`}
        id={`credential-${id}-detail`}
        key={id}
        label={label}
        value={inputs[id]}
        helpText={help_text}
      />
    );
  };

  useEffect(() => {
    fetchDetails();
  }, [fetchDetails]);

  const deleteDetailsRequests =
    relatedResourceDeleteRequests.credential(credential);

  const enabledBooleanFields = fields.filter(
    ({ id, type }) => type === 'boolean' && inputs[id]
  );

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
          dataCy="credential-name-detail"
          id="credential-name-detail"
          label={t`Name`}
          value={name}
        />
        <Detail
          dataCy="credential-description-detail"
          id="credential-description-detail"
          label={t`Description`}
          value={description}
        />
        {organization && (
          <Detail
            dataCy="credential-organization-detail"
            id="credential-organization-detail"
            label={t`Organization`}
            value={
              <Link to={`/organizations/${organization.id}/details`}>
                {organization.name}
              </Link>
            }
          />
        )}
        <Detail
          dataCy="credential-credential_type-detail"
          id="credential-credential_type-detail"
          label={t`Credential Type`}
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

        {fields.map((field) => renderDetail(field))}

        <UserDateDetail
          id="credential-created-detail"
          label={t`Created`}
          date={created}
          user={created_by}
        />
        <UserDateDetail
          id="credential-last_modified-detail"
          label={t`Last Modified`}
          date={modified}
          user={modified_by}
        />
        <Detail
          label={t`Enabled Options`}
          value={
            <TextList component={TextListVariants.ul}>
              {enabledBooleanFields.map(({ id, label }) => (
                <TextListItem key={id} component={TextListItemVariants.li}>
                  {label}
                </TextListItem>
              ))}
            </TextList>
          }
          isEmpty={enabledBooleanFields.length === 0}
        />
      </DetailList>
      {Object.keys(inputSources).length > 0 && (
        <PluginFieldText>
          {t`* This field will be retrieved from an external secret management system using the specified credential.`}
        </PluginFieldText>
      )}
      <CardActionsRow>
        {user_capabilities.edit && (
          <Button
            ouiaId="credential-detail-edit-button"
            component={Link}
            to={`/credentials/${credentialId}/edit`}
          >
            {t`Edit`}
          </Button>
        )}
        {user_capabilities.delete && (
          <DeleteButton
            name={name}
            itemToDelete={credential}
            modalTitle={t`Delete Credential`}
            onConfirm={deleteCredential}
            isLoading={isLoading}
            deleteDetailsRequests={deleteDetailsRequests}
            deleteMessage={t`This credential is currently being used by other resources. Are you sure you want to delete it?`}
          >
            {t`Delete`}
          </DeleteButton>
        )}
      </CardActionsRow>
      {error && (
        <AlertModal
          isOpen={error}
          variant="error"
          title={t`Error!`}
          onClose={dismissError}
        >
          {t`Failed to delete credential.`}
          <ErrorDetail error={error} />
        </AlertModal>
      )}
    </CardBody>
  );
}

CredentialDetail.propTypes = {
  credential: Credential.isRequired,
};

export default CredentialDetail;
