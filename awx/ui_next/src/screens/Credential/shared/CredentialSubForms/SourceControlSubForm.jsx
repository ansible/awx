import React from 'react';
import { withI18n } from '@lingui/react';
import {
  FormColumnLayout,
  FormFullWidthLayout,
} from '../../../../components/FormLayout';
import {
  UsernameFormField,
  PasswordFormField,
  SSHKeyUnlockField,
  SSHKeyDataField,
} from './SharedFields';

const SourceControlSubForm = () => (
  <FormColumnLayout>
    <UsernameFormField />
    <PasswordFormField />
    <SSHKeyUnlockField />
    <FormFullWidthLayout>
      <SSHKeyDataField />
    </FormFullWidthLayout>
  </FormColumnLayout>
);

export default withI18n()(SourceControlSubForm);
