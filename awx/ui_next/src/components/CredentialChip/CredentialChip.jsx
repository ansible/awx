import React from 'react';
import { shape } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Chip } from '@patternfly/react-core';
import { Credential } from '../../types';
import { toTitleCase } from '../../util/strings';

function CredentialChip({ credential, i18n, i18nHash, ...props }) {
  let type;
  if (credential.cloud) {
    type = i18n._(t`Cloud`);
  } else if (credential.kind === 'aws' || credential.kind === 'ssh') {
    type = credential.kind.toUpperCase();
  } else {
    type = toTitleCase(credential.kind);
  }

  return (
    <Chip {...props}>
      <strong>{type}: </strong>
      {credential.name}
    </Chip>
  );
}
CredentialChip.propTypes = {
  credential: Credential.isRequired,
  i18n: shape({}).isRequired,
};

export { CredentialChip as _CredentialChip };
export default withI18n()(CredentialChip);
