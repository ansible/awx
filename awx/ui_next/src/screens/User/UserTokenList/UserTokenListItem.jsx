import React from 'react';
import { Link, useParams } from 'react-router-dom';
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

import { formatDateString } from '../../../util/dates';
import DataListCell from '../../../components/DataListCell';

const Label = styled.b`
  margin-right: 20px;
`;

const NameLabel = styled.b`
  margin-right: 5px;
`;

function UserTokenListItem({ i18n, token, isSelected, onSelect }) {
  const { id } = useParams();
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
            <DataListCell aria-label={i18n._(t`Token type`)} key="type">
              <Link to={`/users/${id}/tokens/${token.id}/details`}>
                {token.summary_fields?.application
                  ? i18n._(t`Application access token`)
                  : i18n._(t`Personal access token`)}
              </Link>
            </DataListCell>,
            <DataListCell
              aria-label={i18n._(t`Application name`)}
              key="applicationName"
            >
              {token.summary_fields?.application && (
                <span>
                  <NameLabel>{i18n._(t`Application`)}</NameLabel>
                  <Link
                    to={`/applications/${token.summary_fields.application.id}/details`}
                  >
                    {token.summary_fields.application.name}
                  </Link>
                </span>
              )}
            </DataListCell>,
            <DataListCell aria-label={i18n._(t`Scope`)} key="scope">
              <Label>{i18n._(t`Scope`)}</Label>
              {toTitleCase(token.scope)}
            </DataListCell>,
            <DataListCell aria-label={i18n._(t`Expiration`)} key="expiration">
              <Label>{i18n._(t`Expires`)}</Label>
              {formatDateString(token.expires)}
            </DataListCell>,
          ]}
        />
      </DataListItemRow>
    </DataListItem>
  );
}

export default withI18n()(UserTokenListItem);
