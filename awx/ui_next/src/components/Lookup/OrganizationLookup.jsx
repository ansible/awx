import React from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { string, func, bool } from 'prop-types';
import { OrganizationsAPI } from '@api';
import { Organization } from '@types';
import { FormGroup } from '@patternfly/react-core';
import Lookup from '@components/Lookup';

const getOrganizations = async params => OrganizationsAPI.read(params);

function OrganizationLookup({
  helperTextInvalid,
  i18n,
  isValid,
  onBlur,
  onChange,
  required,
  value,
}) {
  return (
    <FormGroup
      fieldId="organization"
      helperTextInvalid={helperTextInvalid}
      isRequired={required}
      isValid={isValid}
      label={i18n._(t`Organization`)}
    >
      <Lookup
        id="organization"
        lookupHeader={i18n._(t`Organization`)}
        name="organization"
        value={value}
        onBlur={onBlur}
        onLookupSave={onChange}
        getItems={getOrganizations}
        required={required}
        sortedColumnKey="name"
      />
    </FormGroup>
  );
}

OrganizationLookup.propTypes = {
  helperTextInvalid: string,
  isValid: bool,
  onBlur: func,
  onChange: func.isRequired,
  required: bool,
  value: Organization,
};

OrganizationLookup.defaultProps = {
  helperTextInvalid: '',
  isValid: true,
  onBlur: () => {},
  required: false,
  value: null,
};

export default withI18n()(OrganizationLookup);
export { OrganizationLookup as _OrganizationLookup };
