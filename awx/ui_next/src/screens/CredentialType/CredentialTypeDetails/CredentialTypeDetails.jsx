import React, { useCallback } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Link, useHistory } from 'react-router-dom';
import { Button } from '@patternfly/react-core';

import { VariablesDetail } from '../../../components/CodeMirrorInput';
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

  const { error, dismissError } = useDismissableError(deleteError);

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
              isDisabled={isLoading}
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
        />
      )}
    </CardBody>
  );
}

export default withI18n()(CredentialTypeDetails);
