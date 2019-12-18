import React, { useState } from 'react';
import { t } from '@lingui/macro';

import { CardBody, Button } from '@patternfly/react-core';
import { withI18n } from '@lingui/react';
import { withRouter } from 'react-router-dom';
import styled from 'styled-components';
import { VariablesDetail } from '@components/CodeMirrorInput';
import ErrorDetail from '@components/ErrorDetail';
import AlertModal from '@components/AlertModal';

import { GroupsAPI } from '@api';
import { DetailList, Detail, UserDateDetail } from '@components/DetailList';

// TODO: extract this into a component for use in all relevant Detail views
const ActionButtonWrapper = styled.div`
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
  & > :not(:first-child) {
    margin-left: 20px;
  }
`;

function InventoryGroupDetail({ i18n, history, match, inventoryGroup }) {
  const {
    summary_fields: { created_by, modified_by },
    created,
    modified,
    name,
    description,
    variables,
  } = inventoryGroup;
  const [error, setError] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);

  const handleDelete = async () => {
    setIsDeleteModalOpen(false);
    try {
      await GroupsAPI.destroy(inventoryGroup.id);
      history.push(`/inventories/inventory/${match.params.id}/groups`);
    } catch (err) {
      setError(err);
    }
  };

  return (
    <CardBody>
      <DetailList gutter="sm">
        <Detail label={i18n._(t`Name`)} value={name} />
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
          onClick={() => setIsDeleteModalOpen(true)}
        >
          {i18n._(t`Delete`)}
        </Button>
      </ActionButtonWrapper>
      {isDeleteModalOpen && (
        <AlertModal
          variant="danger"
          title={i18n._(t`Delete Inventory Group`)}
          isOpen={isDeleteModalOpen}
          onClose={() => setIsDeleteModalOpen(false)}
          actions={[
            <Button
              key="delete"
              variant="danger"
              aria-label={i18n._(t`confirm delete`)}
              onClick={handleDelete}
            >
              {i18n._(t`Delete`)}
            </Button>,
            <Button
              key="cancel"
              variant="secondary"
              aria-label={i18n._(t`cancel delete`)}
              onClick={() => setIsDeleteModalOpen(false)}
            >
              {i18n._(t`Cancel`)}
            </Button>,
          ]}
        >
          {i18n._(t`Are you sure you want to delete:`)}
          <br />
          <strong>{inventoryGroup.name}</strong>
          <br />
        </AlertModal>
      )}
      {error && (
        <AlertModal
          variant="danger"
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
export default withI18n()(withRouter(InventoryGroupDetail));
