import React, { useCallback } from 'react';

import { t } from '@lingui/macro';
import { Link, useHistory } from 'react-router-dom';
import { Button, Label } from '@patternfly/react-core';

import AlertModal from 'components/AlertModal';
import { CardBody, CardActionsRow } from 'components/Card';
import DeleteButton from 'components/DeleteButton';
import { Detail, DetailList, UserDateDetail } from 'components/DetailList';
import useRequest, { useDismissableError } from 'hooks/useRequest';
import { toTitleCase } from 'util/strings';
import { ExecutionEnvironmentsAPI } from 'api';
import { relatedResourceDeleteRequests } from 'util/getRelatedResourceDeleteDetails';
import helpText from '../shared/ExecutionEnvironment.helptext';

function ExecutionEnvironmentDetails({ executionEnvironment }) {
  const history = useHistory();
  const {
    id,
    name,
    image,
    description,
    pull,
    organization,
    summary_fields,
    managed: managedByTower,
  } = executionEnvironment;

  const {
    request: deleteExecutionEnvironment,
    isLoading,
    error: deleteError,
  } = useRequest(
    useCallback(async () => {
      await ExecutionEnvironmentsAPI.destroy(id);
      history.push(`/execution_environments`);
    }, [id, history])
  );

  const { error, dismissError } = useDismissableError(deleteError);
  const deleteDetailsRequests =
    relatedResourceDeleteRequests.executionEnvironment(executionEnvironment);
  return (
    <CardBody>
      <DetailList>
        <Detail
          label={t`Name`}
          value={name}
          dataCy="execution-environment-detail-name"
        />
        <Detail
          label={t`Image`}
          value={image}
          dataCy="execution-environment-detail-image"
          helpText={helpText.image}
        />
        <Detail
          label={t`Description`}
          value={description}
          dataCy="execution-environment-detail-description"
        />
        <Detail
          label={t`Managed`}
          value={managedByTower ? t`True` : t`False`}
          dataCy="execution-environment-managed-by-tower"
        />
        <Detail
          label={t`Organization`}
          value={
            organization ? (
              <Link
                to={`/organizations/${summary_fields.organization.id}/details`}
              >
                {summary_fields.organization.name}
              </Link>
            ) : (
              t`Globally Available`
            )
          }
          dataCy="execution-environment-detail-organization"
        />

        <Detail
          label={t`Pull`}
          value={pull === '' ? t`Missing` : toTitleCase(pull)}
          dataCy="execution-environment-pull"
        />
        {executionEnvironment.summary_fields.credential && (
          <Detail
            label={t`Registry credential`}
            value={
              <Label variant="outline" color="blue">
                {executionEnvironment.summary_fields.credential.name}
              </Label>
            }
            dataCy="execution-environment-credential"
            helpText={helpText.registryCredential}
          />
        )}
        <UserDateDetail
          label={t`Created`}
          date={executionEnvironment.created}
          user={executionEnvironment.summary_fields.created_by}
        />
        <UserDateDetail
          label={t`Last Modified`}
          date={executionEnvironment.modified}
          user={executionEnvironment.summary_fields.modified_by}
        />
      </DetailList>
      <CardActionsRow>
        {summary_fields.user_capabilities?.edit && (
          <Button
            ouiaId="execution-environment-detail-edit-button"
            aria-label={t`edit`}
            component={Link}
            to={`/execution_environments/${id}/edit`}
          >
            {t`Edit`}
          </Button>
        )}
        {summary_fields.user_capabilities?.delete && (
          <DeleteButton
            name={image}
            modalTitle={t`Delete Execution Environment`}
            onConfirm={deleteExecutionEnvironment}
            isDisabled={isLoading}
            ouiaId="delete-button"
            deleteDetailsRequests={deleteDetailsRequests}
            deleteMessage={t`This execution environment is currently being used by other resources. Are you sure you want to delete it?`}
          >
            {t`Delete`}
          </DeleteButton>
        )}
      </CardActionsRow>

      {error && (
        <AlertModal
          isOpen={error}
          onClose={dismissError}
          title={t`Error`}
          variant="error"
        />
      )}
    </CardBody>
  );
}

export default ExecutionEnvironmentDetails;
