import React, { useState } from 'react';
import { t } from '@lingui/macro';

import { Button } from '@patternfly/react-core';

import { useHistory, useParams } from 'react-router-dom';
import { VariablesDetail } from 'components/CodeEditor';
import { CardBody, CardActionsRow } from 'components/Card';
import ErrorDetail from 'components/ErrorDetail';
import AlertModal from 'components/AlertModal';
import { DetailList, Detail, UserDateDetail } from 'components/DetailList';
import InventoryGroupsDeleteModal from '../shared/InventoryGroupsDeleteModal';

function InventoryGroupDetail({ inventoryGroup }) {
  const {
    summary_fields: { created_by, modified_by, user_capabilities },
    created,
    modified,
    name,
    description,
    variables,
  } = inventoryGroup;
  const [error, setError] = useState(false);
  const history = useHistory();
  const params = useParams();

  return (
    <CardBody>
      <DetailList gutter="sm">
        <Detail
          label={t`Name`}
          value={name}
          dataCy="inventory-group-detail-name"
        />
        <Detail label={t`Description`} value={description} />
        <VariablesDetail
          label={t`Variables`}
          value={variables}
          rows={4}
          name="variables"
        />
        <UserDateDetail label={t`Created`} date={created} user={created_by} />
        <UserDateDetail
          label={t`Last Modified`}
          date={modified}
          user={modified_by}
        />
      </DetailList>
      <CardActionsRow>
        {user_capabilities?.edit && (
          <Button
            ouiaId="inventory-group-detail-edit-button"
            variant="primary"
            aria-label={t`Edit`}
            onClick={() =>
              history.push(
                `/inventories/inventory/${params.id}/groups/${params.groupId}/edit`
              )
            }
          >
            {t`Edit`}
          </Button>
        )}
        {user_capabilities?.delete && (
          <InventoryGroupsDeleteModal
            groups={[inventoryGroup]}
            isDisabled={false}
            onAfterDelete={() =>
              history.push(`/inventories/inventory/${params.id}/groups`)
            }
          />
        )}
      </CardActionsRow>
      {error && (
        <AlertModal
          variant="error"
          title={t`Error!`}
          isOpen={error}
          onClose={() => setError(false)}
        >
          {t`Failed to delete group ${inventoryGroup.name}.`}
          <ErrorDetail error={error} />
        </AlertModal>
      )}
    </CardBody>
  );
}
export default InventoryGroupDetail;
