import React, { useState, useEffect, useCallback } from 'react';
import { Link, useHistory } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { shape } from 'prop-types';

import { Button, List, ListItem } from '@patternfly/react-core';
import AlertModal from '../../../components/AlertModal';
import { CardBody, CardActionsRow } from '../../../components/Card';
import ContentError from '../../../components/ContentError';
import ContentLoading from '../../../components/ContentLoading';
import DeleteButton from '../../../components/DeleteButton';
import {
  DetailList,
  Detail,
  UserDateDetail,
} from '../../../components/DetailList';
import ErrorDetail from '../../../components/ErrorDetail';
import { CredentialsAPI, CredentialTypesAPI } from '../../../api';
import { Credential } from '../../../types';
import useRequest, { useDismissableError } from '../../../util/useRequest';

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

  const [fields, setFields] = useState([]);
  const [managedByTower, setManagedByTower] = useState([]);
  const [contentError, setContentError] = useState(null);
  const [hasContentLoading, setHasContentLoading] = useState(true);
  const history = useHistory();

  useEffect(() => {
    (async () => {
      setContentError(null);
      setHasContentLoading(true);
      try {
        const {
          data: { inputs: credentialTypeInputs, managed_by_tower },
        } = await CredentialTypesAPI.readDetail(credential_type.id);

        setFields(credentialTypeInputs.fields || []);
        setManagedByTower(managed_by_tower);
      } catch (error) {
        setContentError(error);
      } finally {
        setHasContentLoading(false);
      }
    })();
  }, [credential_type]);

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

  const renderDetail = ({ id, label, type }) => {
    let detail;

    if (type === 'boolean') {
      detail = (
        <Detail
          key={id}
          label={i18n._(t`Options`)}
          value={<List>{inputs[id] && <ListItem>{label}</ListItem>}</List>}
        />
      );
    } else if (inputs[id] === '$encrypted$') {
      const isEncrypted = true;
      detail = (
        <Detail
          key={id}
          label={label}
          value={i18n._(t`Encrypted`)}
          isEncrypted={isEncrypted}
        />
      );
    } else {
      detail = <Detail key={id} label={label} value={inputs[id]} />;
    }

    return detail;
  };

  if (hasContentLoading) {
    return <ContentLoading />;
  }

  if (contentError) {
    return <ContentError error={contentError} />;
  }

  return (
    <CardBody>
      <DetailList>
        <Detail label={i18n._(t`Name`)} value={name} />
        <Detail label={i18n._(t`Description`)} value={description} />
        {organization && (
          <Detail
            label={i18n._(t`Organization`)}
            value={
              <Link to={`/organizations/${organization.id}/details`}>
                {organization.name}
              </Link>
            }
          />
        )}
        <Detail
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
          label={i18n._(t`Created`)}
          date={created}
          user={created_by}
        />
        <UserDateDetail
          label={i18n._(t`Last Modified`)}
          date={modified}
          user={modified_by}
        />
      </DetailList>
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
