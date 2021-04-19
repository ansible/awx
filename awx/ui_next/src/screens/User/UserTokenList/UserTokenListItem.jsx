import React from 'react';
import { Link, useParams } from 'react-router-dom';

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

function UserTokenListItem({ token, isSelected, onSelect }) {
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
            <DataListCell aria-label={t`Token type`} key="type">
              <Link to={`/users/${id}/tokens/${token.id}/details`}>
                {token.summary_fields?.application
                  ? t`Application access token`
                  : t`Personal access token`}
              </Link>
            </DataListCell>,
            <DataListCell
              aria-label={t`Application name`}
              key="applicationName"
            >
              {token.summary_fields?.application && (
                <span>
                  <NameLabel>{t`Application`}</NameLabel>
                  <Link
                    to={`/applications/${token.summary_fields.application.id}/details`}
                  >
                    {token.summary_fields.application.name}
                  </Link>
                </span>
              )}
            </DataListCell>,
            <DataListCell aria-label={t`Scope`} key="scope">
              <Label>{t`Scope`}</Label>
              {toTitleCase(token.scope)}
            </DataListCell>,
            <DataListCell aria-label={t`Expiration`} key="expiration">
              <Label>{t`Expires`}</Label>
              {formatDateString(token.expires)}
            </DataListCell>,
          ]}
        />
      </DataListItemRow>
    </DataListItem>
  );
}

export default UserTokenListItem;
