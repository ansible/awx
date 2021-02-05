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

function ExecutionEnvironmentDetails({ executionEnvironment, i18n }) {
  const history = useHistory();
  const {
    id,
    name,
    image,
    description,
    container_options,
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
        <Detail label={i18n._(t`Description`)} value={description} />
        <Detail
          label={i18n._(t`Container Options`)}
          value={
            container_options === ''
              ? i18n._(t`Missing`)
              : toTitleCase(container_options)
          }
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
        />
        <UserDateDetail
          label={i18n._(t`Last Modified`)}
          date={executionEnvironment.modified}
          user={executionEnvironment.summary_fields.modified_by}
        />
      </DetailList>
      <CardActionsRow>
        <Button
          aria-label={i18n._(t`edit`)}
          component={Link}
          to={`/execution_environments/${id}/edit`}
        >
          {i18n._(t`Edit`)}
        </Button>
        <DeleteButton
          name={image}
          modalTitle={i18n._(t`Delete Execution Environment`)}
          onConfirm={deleteExecutionEnvironment}
          isDisabled={isLoading}
        >
          {i18n._(t`Delete`)}
        </DeleteButton>
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

export default withI18n()(ExecutionEnvironmentDetails);
