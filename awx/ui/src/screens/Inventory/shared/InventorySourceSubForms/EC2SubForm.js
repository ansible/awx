import React, { useCallback } from 'react';
import { useField, useFormikContext } from 'formik';
import { t } from '@lingui/macro';
import getDocsBaseUrl from 'util/getDocsBaseUrl';
import { useConfig } from 'contexts/Config';
import CredentialLookup from 'components/Lookup/CredentialLookup';
import {
  OptionsField,
  SourceVarsField,
  VerbosityField,
  EnabledVarField,
  EnabledValueField,
  HostFilterField,
} from './SharedFields';
import getInventoryHelpTextStrings from '../Inventory.helptext';

const EC2SubForm = () => {
  const { setFieldValue, setFieldTouched } = useFormikContext();
  const [credentialField, credentialMeta] = useField('credential');
  const config = useConfig();
  const handleCredentialUpdate = useCallback(
    (value) => {
      setFieldValue('credential', value);
      setFieldTouched('credential', true, false);
    },
    [setFieldValue, setFieldTouched]
  );

  const helpText = getInventoryHelpTextStrings(
    'ec2',
    `${getDocsBaseUrl(
      config
    )}/html/userguide/inventories.html#inventory-plugins`
  );

  return (
    <>
      <CredentialLookup
        helperTextInvalid={credentialMeta.error}
        isValid={!credentialMeta.touched || !credentialMeta.error}
        credentialTypeNamespace="aws"
        label={t`Credential`}
        value={credentialField.value}
        onChange={handleCredentialUpdate}
      />
      <VerbosityField />
      <HostFilterField />
      <EnabledVarField />
      <EnabledValueField />
      <OptionsField />
      <SourceVarsField popoverContent={helpText.sourceVars} />
    </>
  );
};

export default EC2SubForm;
