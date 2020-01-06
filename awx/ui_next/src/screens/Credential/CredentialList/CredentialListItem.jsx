import React from 'react';
import { string, bool, func } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Link } from 'react-router-dom';
import {
  DataListItem,
  DataListItemRow,
  DataListItemCells as _DataListItemCells,
  Tooltip,
} from '@patternfly/react-core';
import { PencilAltIcon } from '@patternfly/react-icons';

import ActionButtonCell from '@components/ActionButtonCell';
import DataListCell from '@components/DataListCell';
import DataListCheck from '@components/DataListCheck';
import ListActionButton from '@components/ListActionButton';
import VerticalSeparator from '@components/VerticalSeparator';
import styled from 'styled-components';
import { Credential } from '@types';

const DataListItemCells = styled(_DataListItemCells)`
  ${DataListCell}:first-child {
    flex-grow: 2;
  }
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
              <VerticalSeparator />
              <Link to={`${detailUrl}`}>
                <b>{credential.name}</b>
              </Link>
            </DataListCell>,
            <DataListCell key="type">
              {credential.summary_fields.credential_type.name}
            </DataListCell>,
            <ActionButtonCell lastcolumn="true" key="action">
              {canEdit && (
                <Tooltip content={i18n._(t`Edit Credential`)} position="top">
                  <ListActionButton
                    variant="plain"
                    component={Link}
                    to={`/credentials/${credential.id}/edit`}
                  >
                    <PencilAltIcon />
                  </ListActionButton>
                </Tooltip>
              )}
            </ActionButtonCell>,
          ]}
        />
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
