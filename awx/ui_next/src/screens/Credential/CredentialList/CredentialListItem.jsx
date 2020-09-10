import React, { useState, useCallback } from 'react';
import { string, bool, func } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Link } from 'react-router-dom';
import {
  Button,
  DataListAction as _DataListAction,
  DataListCheck,
  DataListItem,
  DataListItemRow,
  DataListItemCells,
  Tooltip,
} from '@patternfly/react-core';
import { PencilAltIcon } from '@patternfly/react-icons';
import styled from 'styled-components';
import DataListCell from '../../../components/DataListCell';
import { timeOfDay } from '../../../util/dates';

import { Credential } from '../../../types';
import { CredentialsAPI } from '../../../api';
import CopyButton from '../../../components/CopyButton';

const DataListAction = styled(_DataListAction)`
  align-items: center;
  display: grid;
  grid-gap: 16px;
  grid-template-columns: repeat(2, 40px);
`;

function CredentialListItem({
  credential,
  detailUrl,
  isSelected,
  onSelect,
  i18n,
  fetchCredentials,
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
    <DataListItem
      key={credential.id}
      aria-labelledby={labelId}
      id={`${credential.id}`}
    >
      <DataListItemRow>
        <DataListCheck
          isDisabled={isDisabled}
          id={`select-credential-${credential.id}`}
          checked={isSelected}
          onChange={onSelect}
          aria-labelledby={labelId}
        />
        <DataListItemCells
          dataListCells={[
            <DataListCell key="name">
              <Link to={`${detailUrl}`}>
                <b>{credential.name}</b>
              </Link>
            </DataListCell>,
            <DataListCell key="type">
              {credential.summary_fields.credential_type.name}
            </DataListCell>,
          ]}
        />
        <DataListAction
          aria-label="actions"
          aria-labelledby={labelId}
          id={labelId}
        >
          {canEdit && (
            <Tooltip content={i18n._(t`Edit Credential`)} position="top">
              <Button
                isDisabled={isDisabled}
                aria-label={i18n._(t`Edit Credential`)}
                variant="plain"
                component={Link}
                to={`/credentials/${credential.id}/edit`}
              >
                <PencilAltIcon />
              </Button>
            </Tooltip>
          )}
          {credential.summary_fields.user_capabilities.copy && (
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
          )}
        </DataListAction>
      </DataListItemRow>
    </DataListItem>
  );
}

CredentialListItem.propTypes = {
  detailUrl: string.isRequired,
  credential: Credential.isRequired,
  isSelected: bool.isRequired,
  onSelect: func.isRequired,
};

export default withI18n()(CredentialListItem);
