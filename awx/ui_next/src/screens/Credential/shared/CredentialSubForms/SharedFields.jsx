import React from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { TextArea, TextInput } from '@patternfly/react-core';
import { CredentialPluginField } from '../CredentialPlugins';
import { PasswordInput } from '../../../../components/FormField';

export const UsernameFormField = withI18n()(({ i18n }) => (
  <CredentialPluginField
    id="credential-username"
    label={i18n._(t`Username`)}
    name="inputs.username"
  >
    <TextInput id="credential-username" />
  </CredentialPluginField>
));

export const PasswordFormField = withI18n()(({ i18n }) => (
  <CredentialPluginField
    id="credential-password"
    label={i18n._(t`Password`)}
    name="inputs.password"
  >
    <PasswordInput id="credential-password" />
  </CredentialPluginField>
));

export const SSHKeyDataField = withI18n()(({ i18n }) => (
  <CredentialPluginField
    id="credential-sshKeyData"
    label={i18n._(t`SSH Private Key`)}
    name="inputs.ssh_key_data"
  >
    <TextArea
      id="credential-sshKeyData"
      rows={6}
      resizeOrientation="vertical"
    />
  </CredentialPluginField>
));

export const SSHKeyUnlockField = withI18n()(({ i18n }) => (
  <CredentialPluginField
    id="credential-sshKeyUnlock"
    label={i18n._(t`Private Key Passphrase`)}
    name="inputs.ssh_key_unlock"
  >
    <PasswordInput id="credential-password" />
  </CredentialPluginField>
));
