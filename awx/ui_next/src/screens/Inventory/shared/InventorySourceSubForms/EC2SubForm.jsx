import React from 'react';
import { useField } from 'formik';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import CredentialLookup from '../../../../components/Lookup/CredentialLookup';
import { OptionsField, SourceVarsField, VerbosityField } from './SharedFields';

const EC2SubForm = ({ i18n }) => {
  const [credentialField, , credentialHelpers] = useField('credential');
  return (
    <>
      <CredentialLookup
        credentialTypeNamespace="aws"
        label={i18n._(t`Credential`)}
        value={credentialField.value}
        onChange={value => {
          credentialHelpers.setValue(value);
        }}
      />
      <VerbosityField />
      <OptionsField />
      <SourceVarsField />
    </>
  );
};

export default withI18n()(EC2SubForm);
