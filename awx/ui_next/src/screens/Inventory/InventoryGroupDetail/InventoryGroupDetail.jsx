import React, { useState } from 'react';
import { t } from '@lingui/macro';

import { Button } from '@patternfly/react-core';
import { withI18n } from '@lingui/react';
import { useHistory, useParams } from 'react-router-dom';
import { VariablesDetail } from '../../../components/CodeMirrorInput';
import { CardBody, CardActionsRow } from '../../../components/Card';
import ErrorDetail from '../../../components/ErrorDetail';
import AlertModal from '../../../components/AlertModal';
import {
  DetailList,
  Detail,
  UserDateDetail,
} from '../../../components/DetailList';
import InventoryGroupsDeleteModal from '../shared/InventoryGroupsDeleteModal';

function InventoryGroupDetail({ i18n, inventoryGroup }) {
  const {
    summary_fields: { created_by, modified_by },
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
          label={i18n._(t`Name`)}
          value={name}
          dataCy="inventory-group-detail-name"
        />
        <Detail label={i18n._(t`Description`)} value={description} />
        <VariablesDetail
          label={i18n._(t`Variables`)}
          value={variables}
          rows={4}
        />
        <UserDateDetail
          label={i18n._(t`Created`)}
          date={created}
          user={created_by}
        />
        <UserDateDetail
          label={i18n._(t`Last Modified`)}
          date={modified}
          user={modified_by}
        />
      </DetailList>
      <CardActionsRow>
        <Button
          variant="primary"
          aria-label={i18n._(t`Edit`)}
          onClick={() =>
            history.push(
              `/inventories/inventory/${params.id}/groups/${params.groupId}/edit`
            )
          }
        >
          {i18n._(t`Edit`)}
        </Button>
        <InventoryGroupsDeleteModal
          groups={[inventoryGroup]}
          isDisabled={false}
          onAfterDelete={() =>
            history.push(`/inventories/inventory/${params.id}/groups`)
          }
        />
      </CardActionsRow>
      {error && (
        <AlertModal
          variant="error"
          title={i18n._(t`Error!`)}
          isOpen={error}
          onClose={() => setError(false)}
        >
          {i18n._(t`Failed to delete group ${inventoryGroup.name}.`)}
          <ErrorDetail error={error} />
        </AlertModal>
      )}
    </CardBody>
  );
}
export default withI18n()(InventoryGroupDetail);
