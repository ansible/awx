import React from 'react';
import { withI18n } from '@lingui/react';
import { bool, func, number, string, oneOfType } from 'prop-types';
import { CredentialsAPI } from '@api';
import { Credential } from '@types';
import { mergeParams } from '@util/qs';
import { FormGroup } from '@patternfly/react-core';
import Lookup from '@components/Lookup';

function CredentialLookup({
  helperTextInvalid,
  label,
  isValid,
  onBlur,
  onChange,
  required,
  credentialTypeId,
  value,
}) {
  const getCredentials = async params =>
    CredentialsAPI.read(
      mergeParams(params, { credential_type: credentialTypeId })
    );

  return (
    <FormGroup
      fieldId="credential"
      isRequired={required}
      isValid={isValid}
      label={label}
      helperTextInvalid={helperTextInvalid}
    >
      <Lookup
        id="credential"
        lookupHeader={label}
        name="credential"
        value={value}
        onBlur={onBlur}
        onLookupSave={onChange}
        getItems={getCredentials}
        required={required}
        sortedColumnKey="name"
      />
    </FormGroup>
  );
}

CredentialLookup.propTypes = {
  credentialTypeId: oneOfType([number, string]).isRequired,
  helperTextInvalid: string,
  isValid: bool,
  label: string.isRequired,
  onBlur: func,
  onChange: func.isRequired,
  required: bool,
  value: Credential,
};

CredentialLookup.defaultProps = {
  helperTextInvalid: '',
  isValid: true,
  onBlur: () => {},
  required: false,
  value: null,
};

export { CredentialLookup as _CredentialLookup };
export default withI18n()(CredentialLookup);
