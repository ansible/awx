import React, { useCallback } from 'react';
import { useField, useFormikContext } from 'formik';
import { t } from '@lingui/macro';
import { useConfig } from 'contexts/Config';
import getDocsBaseUrl from 'util/getDocsBaseUrl';
import CredentialLookup from 'components/Lookup/CredentialLookup';
import { required } from 'util/validators';
import {
  OptionsField,
  VerbosityField,
  EnabledVarField,
  EnabledValueField,
  HostFilterField,
  SourceVarsField,
} from './SharedFields';
import getHelpText from '../Inventory.helptext';

const VirtualizationSubForm = ({ autoPopulateCredential }) => {
  const helpText = getHelpText();
  const { setFieldValue, setFieldTouched } = useFormikContext();
  const [credentialField, credentialMeta, credentialHelpers] =
    useField('credential');
  const config = useConfig();

  const handleCredentialUpdate = useCallback(
    (value) => {
      setFieldValue('credential', value);
      setFieldTouched('credential', true, false);
    },
    [setFieldValue, setFieldTouched]
  );

  const docsBaseUrl = getDocsBaseUrl(config);
  return (
    <>
      <CredentialLookup
        credentialTypeNamespace="rhv"
        label={t`Credential`}
        helperTextInvalid={credentialMeta.error}
        isValid={!credentialMeta.touched || !credentialMeta.error}
        onBlur={() => credentialHelpers.setTouched()}
        onChange={handleCredentialUpdate}
        value={credentialField.value}
        required
        autoPopulate={autoPopulateCredential}
        validate={required(t`Select a value for this field`)}
      />
      <VerbosityField />
      <HostFilterField />
      <EnabledVarField />
      <EnabledValueField />
      <OptionsField />
      <SourceVarsField
        popoverContent={helpText.sourceVars(docsBaseUrl, 'rhv')}
      />
    </>
  );
};

export default VirtualizationSubForm;
