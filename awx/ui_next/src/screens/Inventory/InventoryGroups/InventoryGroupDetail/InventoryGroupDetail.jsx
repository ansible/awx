import React, { useState } from 'react';
import { t } from '@lingui/macro';

import { CardBody, Button } from '@patternfly/react-core';
import { withI18n } from '@lingui/react';
import { withRouter } from 'react-router-dom';
import styled from 'styled-components';
import { VariablesInput } from '@components/CodeMirrorInput';
import ContentError from '@components/ContentError';

import { GroupsAPI } from '@api';
import { DetailList, Detail } from '@components/DetailList';

const ActionButtonWrapper = styled.div`
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
  & > :not(:first-child) {
    margin-left: 20px;
  }
`;
function InventoryGroupDetail({ i18n, history, match, inventoryGroup }) {
  const [error, setError] = useState(false);
  const handleDelete = async () => {
    try {
      await GroupsAPI.destroy(inventoryGroup.id);
      history.push(`/inventories/inventory/${match.params.id}/groups`);
    } catch (err) {
      setError(err);
    }
  };

  if (error) {
    return <ContentError />;
  }
  return (
    <CardBody style={{ paddingTop: '20px' }}>
      <DetailList gutter="sm">
        <Detail label={i18n._(t`Name`)} value={inventoryGroup.name} />
        <Detail
          label={i18n._(t`Description`)}
          value={inventoryGroup.description}
        />
      </DetailList>
      <VariablesInput
        css="margin: 20px 0"
        id="inventoryGroup-variables"
        readOnly
        value={inventoryGroup.variables}
        rows={4}
        label={i18n._(t`Variables`)}
      />
      <DetailList>
        <Detail
          label={i18n._(t`Created`)}
          value={`${inventoryGroup.created} by ${inventoryGroup.summary_fields.created_by.username}`}
        />
        <Detail
          label={i18n._(t`Modified`)}
          value={`${inventoryGroup.modified} by ${inventoryGroup.summary_fields.modified_by.username}`}
        />
      </DetailList>
      <ActionButtonWrapper>
        <Button
          variant="primary"
          aria-label={i18n._(t`Edit`)}
          onClick={() =>
            history.push(
              `/inventories/inventory/${match.params.id}/groups/${inventoryGroup.id}/edit`
            )
          }
        >
          {i18n._(t`Edit`)}
        </Button>
        <Button
          variant="danger"
          aria-label={i18n._(t`Delete`)}
          onClick={handleDelete}
        >
          {i18n._(t`Delete`)}
        </Button>
      </ActionButtonWrapper>
    </CardBody>
  );
}
export default withI18n()(withRouter(InventoryGroupDetail));
