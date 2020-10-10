import React, { useCallback } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Link, useHistory } from 'react-router-dom';
import { Button, Label } from '@patternfly/react-core';

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
import { jsonToYaml, isJsonString } from '../../../util/yaml';
import { InstanceGroupsAPI } from '../../../api';

function ContainerGroupDetails({ instanceGroup, i18n }) {
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

  return (
    <CardBody>
      <DetailList>
        <Detail
          label={i18n._(t`Name`)}
          value={instanceGroup.name}
          dataCy="container-group-detail-name"
        />
        <Detail
          label={i18n._(t`Type`)}
          value={i18n._(t`Container group`)}
          dataCy="container-group-type"
        />
        {instanceGroup.summary_fields.credential && (
          <Detail
            label={i18n._(t`Credential`)}
            value={
              <Label variant="outline" color="blue">
                {instanceGroup.summary_fields.credential?.name}
              </Label>
            }
            dataCy="container-group-credential"
          />
        )}
        <UserDateDetail
          label={i18n._(t`Created`)}
          date={instanceGroup.created}
          user={instanceGroup.summary_fields.created_by}
        />
        <UserDateDetail
          label={i18n._(t`Last Modified`)}
          date={instanceGroup.modified}
          user={instanceGroup.summary_fields.modified_by}
        />
        {instanceGroup.pod_spec_override && (
          <VariablesDetail
            label={i18n._(t`Pod spec override`)}
            value={
              isJsonString(instanceGroup.pod_spec_override)
                ? jsonToYaml(instanceGroup.pod_spec_override)
                : instanceGroup.pod_spec_override
            }
            rows={6}
          />
        )}
      </DetailList>

      <CardActionsRow>
        {instanceGroup.summary_fields.user_capabilities &&
          instanceGroup.summary_fields.user_capabilities.edit && (
            <Button
              aria-label={i18n._(t`edit`)}
              component={Link}
              to={`/instance_groups/container_group/${id}/edit`}
            >
              {i18n._(t`Edit`)}
            </Button>
          )}
        {instanceGroup.summary_fields.user_capabilities &&
          instanceGroup.summary_fields.user_capabilities.delete && (
            <DeleteButton
              name={name}
              modalTitle={i18n._(t`Delete instance group`)}
              onConfirm={deleteInstanceGroup}
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

export default withI18n()(ContainerGroupDetails);
