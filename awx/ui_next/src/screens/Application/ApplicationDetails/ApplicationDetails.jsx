import React, { useCallback } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Link, useHistory } from 'react-router-dom';
import { Button } from '@patternfly/react-core';

import { useDeleteItems } from '../../../util/useRequest';
import AlertModal from '../../../components/AlertModal';
import { CardBody, CardActionsRow } from '../../../components/Card';
import { Detail, DetailList } from '../../../components/DetailList';
import { ApplicationsAPI } from '../../../api';
import DeleteButton from '../../../components/DeleteButton';
import ErrorDetail from '../../../components/ErrorDetail';

function ApplicationDetails({
  i18n,
  application,
  authorizationOptions,
  clientTypeOptions,
}) {
  const history = useHistory();
  const {
    isLoading: deleteLoading,
    deletionError,
    deleteItems: handleDeleteApplications,
    clearDeletionError,
  } = useDeleteItems(
    useCallback(async () => {
      await ApplicationsAPI.destroy(application.id);
      history.push('/applications');
    }, [application.id, history])
  );

  const getAuthorizationGrantType = type => {
    let value;
    authorizationOptions.filter(option => {
      if (option.value === type) {
        value = option.label;
      }
      return null;
    });
    return value;
  };
  const getClientType = type => {
    let value;
    clientTypeOptions.filter(option => {
      if (option.value === type) {
        value = option.label;
      }
      return null;
    });
    return value;
  };
  return (
    <CardBody>
      <DetailList>
        <Detail
          label={i18n._(t`Name`)}
          value={application.name}
          dataCy="jt-detail-name"
        />
        <Detail
          label={i18n._(t`Description`)}
          value={application.description}
        />
        <Detail
          label={i18n._(t`Organization`)}
          value={
            <Link
              to={`/organizations/${application.summary_fields.organization.id}/details`}
            >
              {application.summary_fields.organization.name}
            </Link>
          }
        />
        <Detail
          label={i18n._(t`Authorization grant type`)}
          value={getAuthorizationGrantType(
            application.authorization_grant_type
          )}
        />
        <Detail
          label={i18n._(t`Redirect uris`)}
          value={application.redirect_uris}
        />
        <Detail
          label={i18n._(t`Client type`)}
          value={getClientType(application.client_type)}
        />
      </DetailList>
      <CardActionsRow>
        {application.summary_fields.user_capabilities &&
          application.summary_fields.user_capabilities.edit && (
            <Button
              component={Link}
              to={`/applications/${application.id}/edit`}
              aria-label={i18n._(t`Edit`)}
            >
              {i18n._(t`Edit`)}
            </Button>
          )}
        {application.summary_fields.user_capabilities &&
          application.summary_fields.user_capabilities.delete && (
            <DeleteButton
              name={application.name}
              modalTitle={i18n._(t`Delete application`)}
              onConfirm={handleDeleteApplications}
              isDisabled={deleteLoading}
            >
              {i18n._(t`Delete`)}
            </DeleteButton>
          )}
      </CardActionsRow>
      {deletionError && (
        <AlertModal
          isOpen={deletionError}
          variant="error"
          title={i18n._(t`Error!`)}
          onClose={clearDeletionError}
        >
          {i18n._(t`Failed to delete application.`)}
          <ErrorDetail error={deletionError} />
        </AlertModal>
      )}
    </CardBody>
  );
}
export default withI18n()(ApplicationDetails);
