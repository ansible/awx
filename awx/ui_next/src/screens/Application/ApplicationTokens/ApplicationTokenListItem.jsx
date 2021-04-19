import React from 'react';
import { string, bool, func } from 'prop-types';

import { t } from '@lingui/macro';
import { Link } from 'react-router-dom';
import {
  DataListCheck,
  DataListItem,
  DataListItemCells,
  DataListItemRow,
} from '@patternfly/react-core';
import styled from 'styled-components';

import { Token } from '../../../types';
import { formatDateString } from '../../../util/dates';
import { toTitleCase } from '../../../util/strings';
import DataListCell from '../../../components/DataListCell';

const Label = styled.b`
  margin-right: 20px;
`;

function ApplicationTokenListItem({ token, isSelected, onSelect, detailUrl }) {
  const labelId = `check-action-${token.id}`;
  return (
    <DataListItem key={token.id} aria-labelledby={labelId} id={`${token.id}`}>
      <DataListItemRow>
        <DataListCheck
          id={`select-token-${token.id}`}
          checked={isSelected}
          onChange={onSelect}
          aria-labelledby={labelId}
        />
        <DataListItemCells
          dataListCells={[
            <DataListCell key="divider" aria-label={t`token name`}>
              <Link to={`${detailUrl}`}>
                <b>{token.summary_fields.user.username}</b>
              </Link>
            </DataListCell>,
            <DataListCell key="scope" aria-label={t`scope`}>
              <Label>{t`Scope`}</Label>
              <span>{toTitleCase(token.scope)}</span>
            </DataListCell>,
            <DataListCell key="expiration" aria-label={t`expiration`}>
              <Label>{t`Expiration`}</Label>
              <span>{formatDateString(token.expires)}</span>
            </DataListCell>,
          ]}
        />
      </DataListItemRow>
    </DataListItem>
  );
}

ApplicationTokenListItem.propTypes = {
  token: Token.isRequired,
  detailUrl: string.isRequired,
  isSelected: bool.isRequired,
  onSelect: func.isRequired,
};

export default ApplicationTokenListItem;
