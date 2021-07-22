import React from 'react';
import { Link, useParams } from 'react-router-dom';

import { t } from '@lingui/macro';
import { Tr, Td } from '@patternfly/react-table';
import { toTitleCase } from 'util/strings';
import { formatDateString } from 'util/dates';

function UserTokenListItem({ token, isSelected, onSelect, rowIndex }) {
  const { id } = useParams();
  return (
    <Tr id={`token-row-${token.id}`}>
      <Td
        select={{
          rowIndex,
          isSelected,
          onSelect,
        }}
      />
      <Td dataLabel={t`Name`}>
        <Link to={`/users/${id}/tokens/${token.id}/details`}>
          {token.summary_fields?.application
            ? token.summary_fields.application.name
            : `Personal access token`}
        </Link>
      </Td>
      <Td dataLabel={t`Scope`}>{toTitleCase(token.scope)}</Td>
      <Td dataLabel={t`Expires`}>{formatDateString(token.expires)}</Td>
    </Tr>
  );
}

export default UserTokenListItem;
