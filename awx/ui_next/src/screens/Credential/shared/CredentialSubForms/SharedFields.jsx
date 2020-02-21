import React from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import FormField, { PasswordField } from '@components/FormField';

export const UsernameFormField = withI18n()(({ i18n }) => (
  <FormField
    id="credentual-username"
    label={i18n._(t`Username`)}
    name="inputs.username"
    type="text"
  />
));

export const PasswordFormField = withI18n()(({ i18n }) => (
  <PasswordField
    id="credential-password"
    label={i18n._(t`Password`)}
    name="inputs.password"
  />
));

export const SSHKeyDataField = withI18n()(({ i18n }) => (
  <FormField
    id="credential-sshKeyData"
    label={i18n._(t`SSH Private Key`)}
    name="inputs.ssh_key_data"
    type="textarea"
  />
));

export const SSHKeyUnlockField = withI18n()(({ i18n }) => (
  <PasswordField
    id="credential-sshKeyUnlock"
    label={i18n._(t`Private Key Passphrase`)}
    name="inputs.ssh_key_unlock"
  />
));
