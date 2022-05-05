import React from 'react';
import { Link, useParams } from 'react-router-dom';

import { t } from '@lingui/macro';
import { Tr, Td } from '@patternfly/react-table';
import { toTitleCase } from 'util/strings';
import { formatDateString } from 'util/dates';

function UserTokenListItem({ token, isSelected, onSelect, rowIndex }) {
  const { id } = useParams();
  return (
    <Tr id={`token-row-${token.id}`} ouiaId={`token-row-${token.id}`}>
      <Td
        select={{
          rowIndex,
          isSelected,
          onSelect,
        }}
        dataLabel={t`Selected`}
        id={`token-${token.id}`}
      />
      <Td dataLabel={t`Name`} id={`token-name-${token.id}`}>
        <Link to={`/users/${id}/tokens/${token.id}/details`}>
          {token.summary_fields?.application
            ? token.summary_fields.application.name
            : t`Personal access token`}
        </Link>
      </Td>
      <Td dataLabel={t`Description`} id={`token-description-${token.id}`}>
          {toTitleCase(token.description)}
      </Td>
      <Td dataLabel={t`Scope`} id={`token-scope-${token.id}`}>
        {toTitleCase(token.scope)}
      </Td>
      <Td dataLabel={t`Expires`} id={`token-expires-${token.id}`}>
        {formatDateString(token.expires)}
      </Td>
    </Tr>
  );
}

export default UserTokenListItem;
