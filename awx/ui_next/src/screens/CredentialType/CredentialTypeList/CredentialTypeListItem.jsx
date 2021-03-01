import React from 'react';
import { string, bool, func } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Link } from 'react-router-dom';
import { Button } from '@patternfly/react-core';
import { Tr, Td } from '@patternfly/react-table';
import { PencilAltIcon } from '@patternfly/react-icons';
import { ActionsTd, ActionItem } from '../../../components/PaginatedTable';
import { CredentialType } from '../../../types';

function CredentialTypeListItem({
  credentialType,
  detailUrl,
  isSelected,
  onSelect,
  rowIndex,
  i18n,
}) {
  const labelId = `check-action-${credentialType.id}`;

  return (
    <Tr id={`credential-type-row-${credentialType.id}`}>
      <Td
        select={{
          rowIndex,
          isSelected,
          onSelect,
        }}
        dataLabel={i18n._(t`Selected`)}
      />
      <Td id={labelId} dataLabel={i18n._(t`Name`)}>
        <Link to={`${detailUrl}`}>
          <b>{credentialType.name}</b>
        </Link>
      </Td>
      <ActionsTd dataLabel={i18n._(t`Actions`)}>
        <ActionItem
          visible={credentialType.summary_fields.user_capabilities.edit}
          tooltip={i18n._(t`Edit credential type`)}
        >
          <Button
            aria-label={i18n._(t`Edit credential type`)}
            variant="plain"
            component={Link}
            to={`/credential_types/${credentialType.id}/edit`}
          >
            <PencilAltIcon />
          </Button>
        </ActionItem>
      </ActionsTd>
    </Tr>
  );
}

CredentialTypeListItem.prototype = {
  credentialType: CredentialType.isRequired,
  detailUrl: string.isRequired,
  isSelected: bool.isRequired,
  onSelect: func.isRequired,
};

export default withI18n()(CredentialTypeListItem);
