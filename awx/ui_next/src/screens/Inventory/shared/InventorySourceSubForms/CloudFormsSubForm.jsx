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
import { required } from '../../../../util/validators';

const CloudFormsSubForm = ({ i18n }) => {
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

  const configLink =
    'https://github.com/ansible-collections/community.general/blob/main/scripts/inventory/cloudforms.ini';

  return (
    <>
      <CredentialLookup
        credentialTypeNamespace="cloudforms"
        label={i18n._(t`Credential`)}
        helperTextInvalid={credentialMeta.error}
        isValid={!credentialMeta.touched || !credentialMeta.error}
        onBlur={() => credentialHelpers.setTouched()}
        onChange={handleCredentialUpdate}
        value={credentialField.value}
        required
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
              Override variables found in cloudforms.ini and used by the
              inventory update script. For an example variable configuration{' '}
              <a href={configLink} target="_blank" rel="noopener noreferrer">
                view cloudforms.ini in the Ansible Collections github repo.
              </a>
            </Trans>
            <br />
            <br />
          </>
        }
      />
    </>
  );
};

export default withI18n()(CloudFormsSubForm);
