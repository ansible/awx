import React, { useCallback } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Link, useHistory } from 'react-router-dom';
import { Button } from '@patternfly/react-core';

import useRequest, { useDismissableError } from '../../../util/useRequest';
import AlertModal from '../../../components/AlertModal';
import { CardBody, CardActionsRow } from '../../../components/Card';
import {
  Detail,
  DetailList,
  UserDateDetail,
} from '../../../components/DetailList';
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
    error: deletionError,
    request: deleteApplications,
  } = useRequest(
    useCallback(async () => {
      await ApplicationsAPI.destroy(application.id);
      history.push('/applications');
    }, [application.id, history])
  );

  const { error, dismissError } = useDismissableError(deletionError);

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
          dataCy="app-detail-name"
        />
        <Detail
          label={i18n._(t`Description`)}
          value={application.description}
          dataCy="app-detail-description"
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
          dataCy="app-detail-organization"
        />
        <Detail
          label={i18n._(t`Authorization grant type`)}
          value={getAuthorizationGrantType(
            application.authorization_grant_type
          )}
          dataCy="app-detail-authorization-grant-type"
        />
        <Detail
          label={i18n._(t`Client ID`)}
          value={application.client_id}
          dataCy="app-detail-client-id"
        />
        <Detail
          label={i18n._(t`Redirect uris`)}
          value={application.redirect_uris}
          dataCy="app-detail-redirect-uris"
        />
        <Detail
          label={i18n._(t`Client type`)}
          value={getClientType(application.client_type)}
          dataCy="app-detail-client-type"
        />
        <UserDateDetail label={i18n._(t`Created`)} date={application.created} />
        <UserDateDetail
          label={i18n._(t`Last Modified`)}
          date={application.modified}
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
              onConfirm={deleteApplications}
              isDisabled={deleteLoading}
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
          {i18n._(t`Failed to delete application.`)}
          <ErrorDetail error={error} />
        </AlertModal>
      )}
    </CardBody>
  );
}
export default withI18n()(ApplicationDetails);
