import React, { useCallback } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Link, useHistory } from 'react-router-dom';
import { Button, Label } from '@patternfly/react-core';

import AlertModal from '../../../components/AlertModal';
import { CardBody, CardActionsRow } from '../../../components/Card';
import DeleteButton from '../../../components/DeleteButton';
import {
  Detail,
  DetailList,
  UserDateDetail,
} from '../../../components/DetailList';
import useRequest, { useDismissableError } from '../../../util/useRequest';
import { toTitleCase } from '../../../util/strings';
import { ExecutionEnvironmentsAPI } from '../../../api';
import { relatedResourceDeleteRequests } from '../../../util/getRelatedResourceDeleteDetails';

function ExecutionEnvironmentDetails({ executionEnvironment, i18n }) {
  const history = useHistory();
  const {
    id,
    name,
    image,
    description,
    pull,
    organization,
    summary_fields,
    managed_by_tower: managedByTower,
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
  const deleteDetailsRequests = relatedResourceDeleteRequests.executionEnvironment(
    executionEnvironment,
    i18n
  );
  return (
    <CardBody>
      <DetailList>
        <Detail
          label={i18n._(t`Name`)}
          value={name}
          dataCy="execution-environment-detail-name"
        />
        <Detail
          label={i18n._(t`Image`)}
          value={image}
          dataCy="execution-environment-detail-image"
        />
        <Detail
          label={i18n._(t`Description`)}
          value={description}
          dataCy="execution-environment-detail-description"
        />
        <Detail
          label={i18n._(t`Organization`)}
          value={
            organization ? (
              <Link
                to={`/organizations/${summary_fields.organization.id}/details`}
              >
                {summary_fields.organization.name}
              </Link>
            ) : (
              i18n._(t`Globally Available`)
            )
          }
          dataCy="execution-environment-detail-organization"
        />
        <Detail
          label={i18n._(t`Pull`)}
          value={pull === '' ? i18n._(t`Missing`) : toTitleCase(pull)}
          dataCy="execution-environment-pull"
        />
        {executionEnvironment.summary_fields.credential && (
          <Detail
            label={i18n._(t`Credential`)}
            value={
              <Label variant="outline" color="blue">
                {executionEnvironment.summary_fields.credential.name}
              </Label>
            }
            dataCy="execution-environment-credential"
          />
        )}
        <UserDateDetail
          label={i18n._(t`Created`)}
          date={executionEnvironment.created}
          user={executionEnvironment.summary_fields.created_by}
          dataCy="execution-environment-created"
        />
        <UserDateDetail
          label={i18n._(t`Last Modified`)}
          date={executionEnvironment.modified}
          user={executionEnvironment.summary_fields.modified_by}
          dataCy="execution-environment-modified"
        />
      </DetailList>
      {!managedByTower && (
        <CardActionsRow>
          {summary_fields.user_capabilities?.edit && (
            <Button
              ouiaId="execution-environment-detail-edit-button"
              aria-label={i18n._(t`edit`)}
              component={Link}
              to={`/execution_environments/${id}/edit`}
            >
              {i18n._(t`Edit`)}
            </Button>
          )}
          {summary_fields.user_capabilities?.delete && (
            <DeleteButton
              name={image}
              modalTitle={i18n._(t`Delete Execution Environment`)}
              onConfirm={deleteExecutionEnvironment}
              isDisabled={isLoading}
              ouiaId="delete-button"
              deleteDetailsRequests={deleteDetailsRequests}
              deleteMessage={i18n._(
                t`This execution environment is currently being used by other resources. Are you sure you want to delete it?`
              )}
            >
              {i18n._(t`Delete`)}
            </DeleteButton>
          )}
        </CardActionsRow>
      )}

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

export default withI18n()(ExecutionEnvironmentDetails);
