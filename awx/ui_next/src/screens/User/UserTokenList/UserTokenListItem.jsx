import React from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  DataListItemCells,
  DataListCheck,
  DataListItemRow,
  DataListItem,
} from '@patternfly/react-core';
import styled from 'styled-components';
import { toTitleCase } from '../../../util/strings';

import { formatDateStringUTC } from '../../../util/dates';
import DataListCell from '../../../components/DataListCell';

const Label = styled.b`
  margin-right: 20px;
`;

const NameLabel = styled.b`
  margin-right: 5px;
`;

function UserTokenListItem({ i18n, token, isSelected, onSelect }) {
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
            <DataListCell
              aria-label={i18n._(t`application name`)}
              key={token.id}
            >
              {token.summary_fields?.application?.name ? (
                <span>
                  <NameLabel>{i18n._(t`Application`)}</NameLabel>
                  {token.summary_fields.application.name}
                </span>
              ) : (
                i18n._(t`Personal access token`)
              )}
            </DataListCell>,
            <DataListCell aria-label={i18n._(t`scope`)} key={token.scope}>
              <Label>{i18n._(t`Scope`)}</Label>
              {toTitleCase(token.scope)}
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
