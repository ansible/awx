import React, { useCallback } from 'react';
import { useField, useFormikContext } from 'formik';

import { t, Trans } from '@lingui/macro';
import CredentialLookup from '../../../../components/Lookup/CredentialLookup';
import {
  OptionsField,
  SourceVarsField,
  VerbosityField,
  EnabledVarField,
  EnabledValueField,
  HostFilterField,
} from './SharedFields';
import getDocsBaseUrl from '../../../../util/getDocsBaseUrl';
import { useConfig } from '../../../../contexts/Config';

const EC2SubForm = () => {
  const { setFieldValue } = useFormikContext();
  const [credentialField] = useField('credential');
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
    'https://docs.ansible.com/ansible/latest/collections/amazon/aws/aws_ec2_inventory.html';

  return (
    <>
      <CredentialLookup
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
                aws_ec2
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

export default EC2SubForm;
