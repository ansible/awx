import React from 'react';
import { func } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t, Trans } from '@lingui/macro';
import styled from 'styled-components';
import { Button, ButtonVariant, Tooltip } from '@patternfly/react-core';
import { KeyIcon } from '@patternfly/react-icons';
import CredentialChip from '../../../../components/CredentialChip';
import { Credential } from '../../../../types';

const SelectedCredential = styled.div`
  display: flex;
  justify-content: space-between;
  margin-top: 10px;
  background-color: white;
  border-bottom-color: var(--pf-global--BorderColor--200);
`;

const SpacedCredentialChip = styled(CredentialChip)`
  margin: 5px 8px;
`;

function CredentialPluginSelected({
  i18n,
  credential,
  onEditPlugin,
  onClearPlugin,
}) {
  return (
    <>
      <p>
        <Trans>
          This field will be retrieved from an external secret management system
          using the following credential:
        </Trans>
      </p>
      <SelectedCredential>
        <SpacedCredentialChip onClick={onClearPlugin} credential={credential} />
        <Tooltip
          content={i18n._(t`Edit Credential Plugin Configuration`)}
          position="top"
        >
          <Button
            aria-label={i18n._(t`Edit Credential Plugin Configuration`)}
            onClick={onEditPlugin}
            variant={ButtonVariant.control}
          >
            <KeyIcon />
          </Button>
        </Tooltip>
      </SelectedCredential>
    </>
  );
}

CredentialPluginSelected.propTypes = {
  credential: Credential.isRequired,
  onEditPlugin: func,
  onClearPlugin: func,
};

CredentialPluginSelected.defaultProps = {
  onEditPlugin: () => {},
  onClearPlugin: () => {},
};

export default withI18n()(CredentialPluginSelected);
