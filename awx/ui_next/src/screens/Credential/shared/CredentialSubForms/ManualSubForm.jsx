import React from 'react';
import { useField } from 'formik';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import FormField, { PasswordField } from '@components/FormField';
import { FormGroup } from '@patternfly/react-core';
import AnsibleSelect from '@components/AnsibleSelect';
import { FormColumnLayout, FormFullWidthLayout } from '@components/FormLayout';
import {
  UsernameFormField,
  PasswordFormField,
  SSHKeyUnlockField,
  SSHKeyDataField,
} from './SharedFields';

const ManualSubForm = ({ i18n }) => {
  const becomeMethodOptions = [
    {
      value: '',
      key: '',
      label: i18n._(t`Choose a Privelege Escalation Method`),
      isDisabled: true,
    },
    ...[
      'sudo',
      'su',
      'pbrun',
      'pfexec',
      'dzdo',
      'pmrun',
      'runas',
      'enable',
      'doas',
      'ksu',
      'machinectl',
      'sesu',
    ].map(val => ({ value: val, key: val, label: val })),
  ];

  const becomeMethodFieldArr = useField('inputs.become_method');
  const becomeMethodField = becomeMethodFieldArr[0];
  const becomeMethodHelpers = becomeMethodFieldArr[2];

  return (
    <FormColumnLayout>
      <UsernameFormField />
      <PasswordFormField />
      <FormFullWidthLayout>
        <SSHKeyDataField />
        <FormField
          id="credential-sshPublicKeyData"
          label={i18n._(t`Signed SSH Certificate`)}
          name="inputs.ssh_public_key_data"
          type="textarea"
        />
      </FormFullWidthLayout>
      <SSHKeyUnlockField />
      <FormGroup
        fieldId="credential-becomeMethod"
        label={i18n._(t`Privelege Escalation Method`)}
      >
        <AnsibleSelect
          {...becomeMethodField}
          id="credential-becomeMethod"
          data={becomeMethodOptions}
          onChange={(event, value) => {
            becomeMethodHelpers.setValue(value);
          }}
        />
      </FormGroup>
      <FormField
        id="credential-becomeUsername"
        label={i18n._(t`Privilege Escalation Username`)}
        name="inputs.become_username"
        type="text"
      />
      <PasswordField
        id="credential-becomePassword"
        label={i18n._(t`Privilege Escalation Password`)}
        name="inputs.become_password"
      />
    </FormColumnLayout>
  );
};

export default withI18n()(ManualSubForm);
