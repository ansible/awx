import React, { useCallback } from 'react';
import { useField, useFormikContext } from 'formik';
import { withI18n } from '@lingui/react';
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

const EC2SubForm = ({ i18n }) => {
  const { setFieldValue } = useFormikContext();
  const [credentialField] = useField('credential');

  const handleCredentialUpdate = useCallback(
    value => {
      setFieldValue('credential', value);
    },
    [setFieldValue]
  );

  const pluginLink =
    'http://docs.ansible.com/ansible-tower/latest/html/userguide/inventories.html#inventory-plugins';
  const configLink =
    'https://docs.ansible.com/ansible/latest/collections/amazon/aws/aws_ec2_inventory.html';

  return (
    <>
      <CredentialLookup
        credentialTypeNamespace="aws"
        label={i18n._(t`Credential`)}
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

export default withI18n()(EC2SubForm);
