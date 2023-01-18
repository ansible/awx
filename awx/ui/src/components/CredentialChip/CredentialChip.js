import React from 'react';

import { t } from '@lingui/macro';
import { Chip } from '@patternfly/react-core';
import { Credential } from 'types';
import { toTitleCase } from 'util/strings';

function CredentialChip({ credential, ...props }) {
  let type;
  if (credential.cloud) {
    type = t`Cloud`;
  } else if (credential.kind === 'gpg_public_key') {
    type = t`GPG Public Key`;
  } else if (credential.kind === 'aws' || credential.kind === 'ssh') {
    type = credential.kind.toUpperCase();
  } else {
    type = toTitleCase(credential.kind);
  }

  const buildCredentialName = () => {
    if (credential.kind === 'vault' && credential.inputs?.vault_id) {
      return `${credential.name} | ${credential.inputs.vault_id}`;
    }
    return `${credential.name}`;
  };

  return (
    <Chip {...props}>
      <strong>{type}: </strong>
      {buildCredentialName()}
    </Chip>
  );
}
CredentialChip.propTypes = {
  credential: Credential.isRequired,
};

export { CredentialChip as _CredentialChip };
export default CredentialChip;
