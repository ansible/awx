import React, { useCallback } from 'react';

import { t } from '@lingui/macro';
import { Link, useHistory } from 'react-router-dom';
import styled from 'styled-components';
import { Button } from '@patternfly/react-core';

import AlertModal from 'components/AlertModal';
import { CardBody, CardActionsRow } from 'components/Card';
import ErrorDetail from 'components/ErrorDetail';
import DeleteButton from 'components/DeleteButton';
import {
  Detail,
  DetailList,
  UserDateDetail,
  DetailBadge,
} from 'components/DetailList';
import useRequest, { useDismissableError } from 'hooks/useRequest';
import { InstanceGroupsAPI } from 'api';
import { relatedResourceDeleteRequests } from 'util/getRelatedResourceDeleteDetails';

const Unavailable = styled.span`
  color: var(--pf-global--danger-color--200);
`;

function InstanceGroupDetails({ instanceGroup }) {
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
          dataCy="instance-group-detail-name"
        />
        <Detail
          label={t`Type`}
          value={
            instanceGroup.is_container_group
              ? t`Container group`
              : t`Instance group`
          }
          dataCy="instance-group-type"
        />
        <DetailBadge
          label={t`Policy instance minimum`}
          dataCy="instance-group-policy-instance-minimum"
          content={instanceGroup.policy_instance_minimum}
        />
        <DetailBadge
          label={t`Policy instance percentage`}
          dataCy="instance-group-policy-instance-percentage"
          content={`${instanceGroup.policy_instance_percentage} %`}
        />
        {instanceGroup.capacity ? (
          <DetailBadge
            label={t`Used capacity`}
            content={`${Math.round(
              100 - instanceGroup.percent_capacity_remaining
            )} %`}
            dataCy="instance-group-used-capacity"
          />
        ) : (
          <Detail
            label={t`Used capacity`}
            value={<Unavailable>{t`Unavailable`}</Unavailable>}
            dataCy="instance-group-used-capacity"
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
      </DetailList>

      <CardActionsRow>
        {instanceGroup.summary_fields.user_capabilities &&
          instanceGroup.summary_fields.user_capabilities.edit && (
            <Button
              ouiaId="instance-group-detail-edit-button"
              aria-label={t`edit`}
              component={Link}
              to={`/instance_groups/${id}/edit`}
            >
              {t`Edit`}
            </Button>
          )}
        {instanceGroup.summary_fields.user_capabilities &&
          instanceGroup.summary_fields.user_capabilities.delete && (
            <DeleteButton
              ouiaId="instance-group-detail-delete-button"
              name={name}
              modalTitle={t`Delete instance group`}
              onConfirm={deleteInstanceGroup}
              isDisabled={isLoading}
              deleteDetailsRequests={deleteDetailsRequests}
              deleteMessage={t`This instance group is currently being by other resources. Are you sure you want to delete it?`}
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

export default InstanceGroupDetails;
