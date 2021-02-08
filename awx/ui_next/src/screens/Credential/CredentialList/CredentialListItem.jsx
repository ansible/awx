import React, { useState, useCallback } from 'react';
import { string, bool, func } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Link } from 'react-router-dom';
import { Button } from '@patternfly/react-core';
import { Tr, Td } from '@patternfly/react-table';
import { PencilAltIcon } from '@patternfly/react-icons';
import { ActionsTd, ActionItem } from '../../../components/PaginatedTable';
import { timeOfDay } from '../../../util/dates';

import { Credential } from '../../../types';
import { CredentialsAPI } from '../../../api';
import CopyButton from '../../../components/CopyButton';

function CredentialListItem({
  credential,
  detailUrl,
  isSelected,
  onSelect,
  i18n,
  fetchCredentials,
  rowIndex,
}) {
  const [isDisabled, setIsDisabled] = useState(false);

  const labelId = `check-action-${credential.id}`;
  const canEdit = credential.summary_fields.user_capabilities.edit;

  const copyCredential = useCallback(async () => {
    await CredentialsAPI.copy(credential.id, {
      name: `${credential.name} @ ${timeOfDay()}`,
    });
    await fetchCredentials();
  }, [credential.id, credential.name, fetchCredentials]);

  const handleCopyStart = useCallback(() => {
    setIsDisabled(true);
  }, []);

  const handleCopyFinish = useCallback(() => {
    setIsDisabled(false);
  }, []);

  return (
    <Tr id={`${credential.id}`}>
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
          <b>{credential.name}</b>
        </Link>
      </Td>
      <Td dataLabel={i18n._(t`Type`)}>
        {credential.summary_fields.credential_type.name}
      </Td>
      <ActionsTd dataLabel={i18n._(t`Actions`)}>
        <ActionItem visible={canEdit} tooltip={i18n._(t`Edit Credential`)}>
          <Button
            isDisabled={isDisabled}
            aria-label={i18n._(t`Edit Credential`)}
            variant="plain"
            component={Link}
            to={`/credentials/${credential.id}/edit`}
          >
            <PencilAltIcon />
          </Button>
        </ActionItem>
        <ActionItem visible={credential.summary_fields.user_capabilities.copy}>
          <CopyButton
            isDisabled={isDisabled}
            onCopyStart={handleCopyStart}
            onCopyFinish={handleCopyFinish}
            copyItem={copyCredential}
            helperText={{
              tooltip: i18n._(t`Copy Credential`),
              errorMessage: i18n._(t`Failed to copy credential.`),
            }}
          />
        </ActionItem>
      </ActionsTd>
    </Tr>
  );
}

CredentialListItem.propTypes = {
  detailUrl: string.isRequired,
  credential: Credential.isRequired,
  isSelected: bool.isRequired,
  onSelect: func.isRequired,
};

export default withI18n()(CredentialListItem);
