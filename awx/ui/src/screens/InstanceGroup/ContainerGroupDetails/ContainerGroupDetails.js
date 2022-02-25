import React, { useCallback } from 'react';

import { t } from '@lingui/macro';
import { Link, useHistory } from 'react-router-dom';
import { Button, Label } from '@patternfly/react-core';

import { VariablesDetail } from 'components/CodeEditor';
import AlertModal from 'components/AlertModal';
import ErrorDetail from 'components/ErrorDetail';
import { CardBody, CardActionsRow } from 'components/Card';
import DeleteButton from 'components/DeleteButton';
import { Detail, DetailList, UserDateDetail } from 'components/DetailList';
import useRequest, { useDismissableError } from 'hooks/useRequest';
import { jsonToYaml, isJsonString } from 'util/yaml';
import { InstanceGroupsAPI } from 'api';
import { relatedResourceDeleteRequests } from 'util/getRelatedResourceDeleteDetails';

function ContainerGroupDetails({ instanceGroup }) {
  const { id, name } = instanceGroup;

  const history = useHistory();

  const {
    request: deleteInstanceGroup,
    isLoading,
    error: deleteError,
  } = useRequest(
    useCallback(async () => {
      await InstanceGroupsAPI.destroy(id);
      history.push(`/instance_groups`);
    }, [id, history])
  );

  const { error, dismissError } = useDismissableError(deleteError);
  const deleteDetailsRequests =
    relatedResourceDeleteRequests.instanceGroup(instanceGroup);
  return (
    <CardBody>
      <DetailList>
        <Detail
          label={t`Name`}
          value={instanceGroup.name}
          dataCy="container-group-detail-name"
        />
        <Detail
          label={t`Type`}
          value={t`Container group`}
          dataCy="container-group-type"
        />
        {instanceGroup.summary_fields.credential && (
          <Detail
            label={t`Credential`}
            value={
              <Link
                to={`/credentials/${instanceGroup?.summary_fields?.credential?.id}`}
              >
                <Label variant="outline" color="blue">
                  {instanceGroup?.summary_fields?.credential?.name}
                </Label>
              </Link>
            }
            dataCy="container-group-credential"
          />
        )}
        <UserDateDetail
          label={t`Created`}
          date={instanceGroup.created}
          user={instanceGroup.summary_fields.created_by}
        />
        <UserDateDetail
          label={t`Last Modified`}
          date={instanceGroup.modified}
          user={instanceGroup.summary_fields.modified_by}
        />
        {instanceGroup.pod_spec_override && (
          <VariablesDetail
            label={t`Pod spec override`}
            value={
              isJsonString(instanceGroup.pod_spec_override)
                ? jsonToYaml(instanceGroup.pod_spec_override)
                : instanceGroup.pod_spec_override
            }
            rows={6}
            name="pod_spec_override"
            dataCy="container-group-detail-pod-spec-override"
          />
        )}
      </DetailList>

      <CardActionsRow>
        {instanceGroup.summary_fields.user_capabilities &&
          instanceGroup.summary_fields.user_capabilities.edit && (
            <Button
              ouiaId="container-group-detail-edit-button"
              aria-label={t`edit`}
              component={Link}
              to={`/instance_groups/container_group/${id}/edit`}
            >
              {t`Edit`}
            </Button>
          )}
        {instanceGroup.summary_fields.user_capabilities &&
          instanceGroup.summary_fields.user_capabilities.delete && (
            <DeleteButton
              ouiaId="container-group-detail-delete-button"
              name={name}
              modalTitle={t`Delete instance group`}
              onConfirm={deleteInstanceGroup}
              isDisabled={isLoading}
              deleteDetailsRequests={deleteDetailsRequests}
              deleteMessage={t`This container group is currently being by other resources. Are you sure you want to delete it?`}
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
        >
          <ErrorDetail error={error} />
        </AlertModal>
      )}
    </CardBody>
  );
}

export default ContainerGroupDetails;
