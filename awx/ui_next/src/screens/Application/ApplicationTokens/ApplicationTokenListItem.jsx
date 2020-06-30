import React from 'react';
import { string, bool, func } from 'prop-types';
import { withI18n } from '@lingui/react';
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

function ApplicationTokenListItem({
  token,
  isSelected,
  onSelect,
  detailUrl,
  i18n,
}) {
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
            <DataListCell key="divider" aria-label={i18n._(t`token name`)}>
              <Link to={`${detailUrl}`}>
                <b>{token.summary_fields.user.username}</b>
              </Link>
            </DataListCell>,
            <DataListCell key="scope" aria-label={i18n._(t`scope`)}>
              <Label>{i18n._(t`Scope`)}</Label>
              <span>{toTitleCase(token.scope)}</span>
            </DataListCell>,
            <DataListCell key="expiration" aria-label={i18n._(t`expiration`)}>
              <Label>{i18n._(t`Expiration`)}</Label>
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

export default withI18n()(ApplicationTokenListItem);
