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
import { PencilAltIcon } from '@patternfly/react-icons';
import styled from 'styled-components';

import DataListCell from '../../../components/DataListCell';
import { CredentialType } from '../../../types';

const DataListAction = styled(_DataListAction)`
  align-items: center;
  display: grid;
  grid-gap: 16px;
  grid-template-columns: 40px;
`;

function CredentialTypeListItem({
  credentialType,
  detailUrl,
  isSelected,
  onSelect,
  i18n,
}) {
  const labelId = `check-action-${credentialType.id}`;

  return (
    <DataListItem
      key={credentialType.id}
      aria-labelledby={labelId}
      id={`${credentialType.id} `}
    >
      <DataListItemRow>
        <DataListCheck
          id={`select-credential-types-${credentialType.id}`}
          checked={isSelected}
          onChange={onSelect}
          aria-labelledby={labelId}
        />
        <DataListItemCells
          dataListCells={[
            <DataListCell
              key="name"
              aria-label={i18n._(t`credential type name`)}
            >
              <Link to={`${detailUrl}`}>
                <b>{credentialType.name}</b>
              </Link>
            </DataListCell>,
          ]}
        />
        <DataListAction
          aria-label="actions"
          aria-labelledby={labelId}
          id={labelId}
        >
          {credentialType.summary_fields.user_capabilities.edit && (
            <Tooltip content={i18n._(t`Edit credential type`)} position="top">
              <Button
                aria-label={i18n._(t`Edit credential type`)}
                variant="plain"
                component={Link}
                to={`/credential_types/${credentialType.id}/edit`}
              >
                <PencilAltIcon />
              </Button>
            </Tooltip>
          )}
        </DataListAction>
      </DataListItemRow>
    </DataListItem>
  );
}

CredentialTypeListItem.prototype = {
  credentialType: CredentialType.isRequired,
  detailUrl: string.isRequired,
  isSelected: bool.isRequired,
  onSelect: func.isRequired,
};

export default withI18n()(CredentialTypeListItem);
