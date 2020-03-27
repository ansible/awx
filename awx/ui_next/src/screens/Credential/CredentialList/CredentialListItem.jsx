import React from 'react';
import { string, bool, func } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Link } from 'react-router-dom';
import {
  Button,
  DataListAction as _DataListAction,
  DataListCheck,
  DataListItem,
  DataListItemRow,
  DataListItemCells,
  Tooltip,
} from '@patternfly/react-core';
import DataListCell from '@components/DataListCell';

import { PencilAltIcon } from '@patternfly/react-icons';
import { Credential } from '@types';
import styled from 'styled-components';

const DataListAction = styled(_DataListAction)`
  align-items: center;
  display: grid;
  grid-gap: 16px;
  grid-template-columns: 40px;
`;

function CredentialListItem({
  credential,
  detailUrl,
  isSelected,
  onSelect,
  i18n,
}) {
  const labelId = `check-action-${credential.id}`;
  const canEdit = credential.summary_fields.user_capabilities.edit;

  return (
    <DataListItem
      key={credential.id}
      aria-labelledby={labelId}
      id={`${credential.id}`}
    >
      <DataListItemRow>
        <DataListCheck
          id={`select-credential-${credential.id}`}
          checked={isSelected}
          onChange={onSelect}
          aria-labelledby={labelId}
        />
        <DataListItemCells
          dataListCells={[
            <DataListCell key="name">
              <Link to={`${detailUrl}`}>
                <b>{credential.name}</b>
              </Link>
            </DataListCell>,
            <DataListCell key="type">
              {credential.summary_fields.credential_type.name}
            </DataListCell>,
          ]}
        />
        <DataListAction
          aria-label="actions"
          aria-labelledby={labelId}
          id={labelId}
        >
          {canEdit ? (
            <Tooltip content={i18n._(t`Edit Credential`)} position="top">
              <Button
                aria-label={i18n._(t`Edit Credential`)}
                variant="plain"
                component={Link}
                to={`/credentials/${credential.id}/edit`}
              >
                <PencilAltIcon />
              </Button>
            </Tooltip>
          ) : (
            ''
          )}
        </DataListAction>
      </DataListItemRow>
    </DataListItem>
  );
}

CredentialListItem.propTypes = {
  detailUrl: string.isRequired,
  credential: Credential.isRequired,
  isSelected: bool.isRequired,
  onSelect: func.isRequired,
};

export default withI18n()(CredentialListItem);
