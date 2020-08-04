import React from 'react';
import { useField } from 'formik';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import CredentialLookup from '../../../../components/Lookup/CredentialLookup';
import {
  OptionsField,
  SourceVarsField,
  VerbosityField,
  EnabledVarField,
  EnabledValueField,
  HostFilterField,
} from './SharedFields';

const OpenStackSubForm = ({ i18n }) => {
  const [credentialField, credentialMeta, credentialHelpers] = useField(
    'credential'
  );

  return (
    <>
      <CredentialLookup
        credentialTypeNamespace="openstack"
        label={i18n._(t`Credential`)}
        helperTextInvalid={credentialMeta.error}
        isValid={!credentialMeta.touched || !credentialMeta.error}
        onBlur={() => credentialHelpers.setTouched()}
        onChange={value => {
          credentialHelpers.setValue(value);
        }}
        value={credentialField.value}
        required
      />
      <VerbosityField />
      <HostFilterField />
      <EnabledVarField />
      <EnabledValueField />
      <OptionsField />
      <SourceVarsField />
    </>
  );
};

export default withI18n()(OpenStackSubForm);
