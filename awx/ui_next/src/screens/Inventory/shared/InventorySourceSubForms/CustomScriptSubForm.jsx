import React from 'react';
import { useField } from 'formik';
import { useParams } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import CredentialLookup from '../../../../components/Lookup/CredentialLookup';
import InventoryScriptLookup from '../../../../components/Lookup/InventoryScriptLookup';
import { OptionsField, SourceVarsField, VerbosityField } from './SharedFields';

const CustomScriptSubForm = ({ i18n }) => {
  const { id } = useParams();
  const [credentialField, , credentialHelpers] = useField('credential');
  const [scriptField, scriptMeta, scriptHelpers] = useField('source_script');

  return (
    <>
      <CredentialLookup
        credentialTypeNamespace="cloud"
        label={i18n._(t`Credential`)}
        value={credentialField.value}
        onChange={value => {
          credentialHelpers.setValue(value);
        }}
      />
      <InventoryScriptLookup
        helperTextInvalid={scriptMeta.error}
        isValid={!scriptMeta.touched || !scriptMeta.error}
        onBlur={() => scriptHelpers.setTouched()}
        onChange={value => {
          scriptHelpers.setValue(value);
        }}
        inventoryId={id}
        value={scriptField.value}
        required
      />
      <VerbosityField />
      <OptionsField />
      <SourceVarsField />
    </>
  );
};

export default withI18n()(CustomScriptSubForm);
