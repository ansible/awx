import React, { useCallback, useEffect } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Link, useHistory } from 'react-router-dom';
import { Button } from '@patternfly/react-core';

import { VariablesDetail } from '../../../components/CodeEditor';
import AlertModal from '../../../components/AlertModal';
import { CardBody, CardActionsRow } from '../../../components/Card';
import DeleteButton from '../../../components/DeleteButton';
import {
  Detail,
  DetailList,
  UserDateDetail,
} from '../../../components/DetailList';
import useRequest, { useDismissableError } from '../../../util/useRequest';
import { CredentialTypesAPI } from '../../../api';
import { jsonToYaml } from '../../../util/yaml';
import {
  relatedResourceDeleteRequests,
  getRelatedResourceDeleteCounts,
} from '../../../util/getRelatedResourceDeleteDetails';
import ErrorDetail from '../../../components/ErrorDetail';

function CredentialTypeDetails({ credentialType, i18n }) {
  const { id, name, description, injectors, inputs } = credentialType;
  const history = useHistory();

  const {
    request: deleteCredentialType,
    isLoading,
    error: deleteError,
  } = useRequest(
    useCallback(async () => {
      await CredentialTypesAPI.destroy(id);
      history.push(`/credential_types`);
    }, [id, history])
  );

  const {
    result: { isDeleteDisabled },
    error: deleteDetailsError,
    request: fetchDeleteDetails,
  } = useRequest(
    useCallback(async () => {
      const {
        results: deleteDetails,
        error,
      } = await getRelatedResourceDeleteCounts(
        relatedResourceDeleteRequests.credentialType(credentialType, i18n)
      );
      if (error) {
        throw new Error(error);
      }
      if (deleteDetails) {
        return { isDeleteDisabled: true };
      }
      return { isDeleteDisabled: false };
    }, [credentialType, i18n]),
    { isDeleteDisabled: false }
  );

  useEffect(() => {
    fetchDeleteDetails();
  }, [fetchDeleteDetails]);
  const { error, dismissError } = useDismissableError(
    deleteError || deleteDetailsError
  );

  return (
    <CardBody>
      <DetailList>
        <Detail
          label={i18n._(t`Name`)}
          value={name}
          dataCy="credential-type-detail-name"
        />
        <Detail label={i18n._(t`Description`)} value={description} />
        <VariablesDetail
          label={i18n._(t`Input configuration`)}
          value={jsonToYaml(JSON.stringify(inputs))}
          rows={6}
        />
        <VariablesDetail
          label={i18n._(t`Injector configuration`)}
          value={jsonToYaml(JSON.stringify(injectors))}
          rows={6}
        />
        <UserDateDetail
          label={i18n._(t`Created`)}
          date={credentialType.created}
          user={credentialType.summary_fields.created_by}
        />
        <UserDateDetail
          label={i18n._(t`Last Modified`)}
          date={credentialType.modified}
          user={credentialType.summary_fields.modified_by}
        />
      </DetailList>
      <CardActionsRow>
        {credentialType.summary_fields.user_capabilities &&
          credentialType.summary_fields.user_capabilities.edit && (
            <Button
              ouiaId="credential-type-detail-edit-button"
              aria-label={i18n._(t`edit`)}
              component={Link}
              to={`/credential_types/${id}/edit`}
            >
              {i18n._(t`Edit`)}
            </Button>
          )}
        {credentialType.summary_fields.user_capabilities &&
          credentialType.summary_fields.user_capabilities.delete && (
            <DeleteButton
              name={name}
              modalTitle={i18n._(t`Delete credential type`)}
              onConfirm={deleteCredentialType}
              isDisabled={isLoading || isDeleteDisabled}
              disabledTooltip={
                isDeleteDisabled &&
                i18n._(
                  t`This credential type is currently being used by some credentials and cannot be deleted`
                )
              }
            >
              {i18n._(t`Delete`)}
            </DeleteButton>
          )}
      </CardActionsRow>

      {error && (
        <AlertModal
          isOpen={error}
          onClose={dismissError}
          title={i18n._(t`Error`)}
          variant="error"
        >
          <ErrorDetail error={error} />
        </AlertModal>
      )}
    </CardBody>
  );
}

export default withI18n()(CredentialTypeDetails);
