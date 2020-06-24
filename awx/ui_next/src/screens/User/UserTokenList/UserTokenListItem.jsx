import React from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Link } from 'react-router-dom';
import {
  DataListItemCells,
  DataListCheck,
  DataListItemRow,
  DataListItem,
} from '@patternfly/react-core';
import styled from 'styled-components';

import { formatDateStringUTC } from '../../../util/dates';
import DataListCell from '../../../components/DataListCell';

const Label = styled.b`
  margin-right: 20px;
`;
function UserTokenListItem({ i18n, token, isSelected, detailUrl, onSelect }) {
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
            <DataListCell aria-label={i18n._(t`name`)} key={token.id}>
              <Link to={`${detailUrl}`}>
                {token.summary_fields.application.name}
              </Link>
            </DataListCell>,
            <DataListCell aria-label={i18n._(t`scope`)} key={token.scope}>
              <Label>{i18n._(t`Scope`)}</Label>
              {token.scope}
            </DataListCell>,
            <DataListCell aria-label={i18n._(t`expiration`)} key="expiration">
              <Label>{i18n._(t`Expires`)}</Label>
              {formatDateStringUTC(token.expires)}
            </DataListCell>,
          ]}
        />
      </DataListItemRow>
    </DataListItem>
  );
}

export default withI18n()(UserTokenListItem);
