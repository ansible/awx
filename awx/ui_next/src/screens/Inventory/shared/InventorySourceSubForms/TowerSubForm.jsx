import React, { useCallback } from 'react';
import { useField, useFormikContext } from 'formik';

import { t, Trans } from '@lingui/macro';
import CredentialLookup from '../../../../components/Lookup/CredentialLookup';
import {
  OptionsField,
  VerbosityField,
  EnabledVarField,
  EnabledValueField,
  HostFilterField,
  SourceVarsField,
} from './SharedFields';
import { required } from '../../../../util/validators';
import getDocsBaseUrl from '../../../../util/getDocsBaseUrl';
import { useConfig } from '../../../../contexts/Config';

const TowerSubForm = ({ autoPopulateCredential }) => {
  const { setFieldValue } = useFormikContext();
  const [credentialField, credentialMeta, credentialHelpers] = useField({
    name: 'credential',
    validate: required(t`Select a value for this field`),
  });
  const config = useConfig();

  const handleCredentialUpdate = useCallback(
    value => {
      setFieldValue('credential', value);
    },
    [setFieldValue]
  );

  const pluginLink = `${getDocsBaseUrl(
    config
  )}/html/userguide/inventories.html#inventory-plugins`;
  const configLink =
    'https://docs.ansible.com/ansible/latest/collections/awx/awx/tower_inventory.html';

  return (
    <>
      <CredentialLookup
        credentialTypeNamespace="tower"
        label={t`Credential`}
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
      <SourceVarsField
        popoverContent={
          <>
            <Trans>
              Enter variables to configure the inventory source. For a detailed
              description of how to configure this plugin, see{' '}
              <a href={pluginLink} target="_blank" rel="noopener noreferrer">
                Inventory Plugins
              </a>{' '}
              in the documentation and the{' '}
              <a href={configLink} target="_blank" rel="noopener noreferrer">
                Tower
              </a>{' '}
              plugin configuration guide.
            </Trans>
            <br />
            <br />
          </>
        }
      />
    </>
  );
};

export default TowerSubForm;
