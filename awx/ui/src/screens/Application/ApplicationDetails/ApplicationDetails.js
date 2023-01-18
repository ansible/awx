import React, { useCallback } from 'react';

import { t } from '@lingui/macro';
import { Link, useHistory } from 'react-router-dom';
import { Button } from '@patternfly/react-core';

import useRequest, { useDismissableError } from 'hooks/useRequest';
import AlertModal from 'components/AlertModal';
import { CardBody, CardActionsRow } from 'components/Card';
import { Detail, DetailList, UserDateDetail } from 'components/DetailList';
import { ApplicationsAPI } from 'api';
import DeleteButton from 'components/DeleteButton';
import ErrorDetail from 'components/ErrorDetail';
import getApplicationHelpTextStrings from '../shared/Application.helptext';

function ApplicationDetails({
  application,
  authorizationOptions,
  clientTypeOptions,
}) {
  const applicationHelpTextStrings = getApplicationHelpTextStrings();
  const history = useHistory();
  const {
    isLoading: deleteLoading,
    error: deletionError,
    request: deleteApplications,
  } = useRequest(
    useCallback(async () => {
      await ApplicationsAPI.destroy(application.id);
      history.push('/applications');
    }, [application.id, history])
  );

  const { error, dismissError } = useDismissableError(deletionError);

  const getAuthorizationGrantType = (type) => {
    let value;
    authorizationOptions.filter((option) => {
      if (option.value === type) {
        value = option.label;
      }
      return null;
    });
    return value;
  };
  const getClientType = (type) => {
    let value;
    clientTypeOptions.filter((option) => {
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
          label={t`Name`}
          value={application.name}
          dataCy="app-detail-name"
        />
        <Detail
          label={t`Description`}
          value={application.description}
          dataCy="app-detail-description"
        />
        <Detail
          label={t`Organization`}
          value={
            <Link
              to={`/organizations/${application.summary_fields.organization.id}/details`}
            >
              {application.summary_fields.organization.name}
            </Link>
          }
          dataCy="app-detail-organization"
        />
        <Detail
          label={t`Authorization grant type`}
          value={getAuthorizationGrantType(
            application.authorization_grant_type
          )}
          dataCy="app-detail-authorization-grant-type"
          helpText={applicationHelpTextStrings.authorizationGrantType}
        />
        <Detail
          label={t`Client ID`}
          value={application.client_id}
          dataCy="app-detail-client-id"
        />
        <Detail
          label={t`Redirect URIs`}
          value={application.redirect_uris}
          dataCy="app-detail-redirect-uris"
          helpText={applicationHelpTextStrings.redirectURIS}
        />
        <Detail
          label={t`Client type`}
          value={getClientType(application.client_type)}
          dataCy="app-detail-client-type"
          helpText={applicationHelpTextStrings.clientType}
        />
        <UserDateDetail label={t`Created`} date={application.created} />
        <UserDateDetail label={t`Last Modified`} date={application.modified} />
      </DetailList>
      <CardActionsRow>
        {application.summary_fields.user_capabilities &&
          application.summary_fields.user_capabilities.edit && (
            <Button
              ouiaId="application-details-edit-button"
              component={Link}
              to={`/applications/${application.id}/edit`}
              aria-label={t`Edit`}
            >
              {t`Edit`}
            </Button>
          )}
        {application.summary_fields.user_capabilities &&
          application.summary_fields.user_capabilities.delete && (
            <DeleteButton
              name={application.name}
              modalTitle={t`Delete application`}
              onConfirm={deleteApplications}
              isDisabled={deleteLoading}
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
          {t`Failed to delete application.`}
          <ErrorDetail error={error} />
        </AlertModal>
      )}
    </CardBody>
  );
}
export default ApplicationDetails;
