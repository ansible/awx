import React from 'react';
import { string, bool, func, number } from 'prop-types';
import { t } from '@lingui/macro';
import { Link } from 'react-router-dom';
import { Tr, Td } from '@patternfly/react-table';

import { Token } from 'types';
import { formatDateString } from 'util/dates';
import { toTitleCase } from 'util/strings';

function ApplicationTokenListItem({
  token,
  isSelected,
  onSelect,
  detailUrl,
  rowIndex,
}) {
  return (
    <Tr id={`token-row-${token.id}`} ouiaId={`token-row-${token.id}`}>
      <Td
        select={{
          rowIndex,
          isSelected,
          onSelect,
        }}
        dataLabel={t`Selected`}
      />
      <Td dataLabel={t`Name`}>
        <Link to={detailUrl}>
          <b>{token.summary_fields.user.username}</b>
        </Link>
      </Td>
      <Td dataLabel={t`Scope`}>{toTitleCase(token.scope)}</Td>
      <Td dataLabel={t`Expires`}>{formatDateString(token.expires)}</Td>
    </Tr>
  );
}

ApplicationTokenListItem.propTypes = {
  token: Token.isRequired,
  detailUrl: string.isRequired,
  isSelected: bool.isRequired,
  onSelect: func.isRequired,
  rowIndex: number.isRequired,
};

export default ApplicationTokenListItem;
