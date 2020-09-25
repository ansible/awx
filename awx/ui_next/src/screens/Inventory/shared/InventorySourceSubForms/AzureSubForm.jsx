import React, { useCallback } from 'react';
import { useField, useFormikContext } from 'formik';
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
import { required } from '../../../../util/validators';

const AzureSubForm = ({ autoPopulateCredential, i18n }) => {
  const { setFieldValue } = useFormikContext();
  const [credentialField, credentialMeta, credentialHelpers] = useField({
    name: 'credential',
    validate: required(i18n._(t`Select a value for this field`), i18n),
  });

  const handleCredentialUpdate = useCallback(
    value => {
      setFieldValue('credential', value);
    },
    [setFieldValue]
  );

  return (
    <>
      <CredentialLookup
        credentialTypeNamespace="azure_rm"
        label={i18n._(t`Credential`)}
        helperTextInvalid={credentialMeta.error}
        isValid={!credentialMeta.touched || !credentialMeta.error}
        onBlur={() => credentialHelpers.setTouched()}
        onChange={handleCredentialUpdate}
        value={credentialField.value}
        required
        autoPopulate={autoPopulateCredential}
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

export default withI18n()(AzureSubForm);
