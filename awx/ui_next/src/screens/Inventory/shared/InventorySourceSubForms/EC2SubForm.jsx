import React from 'react';
import { useField } from 'formik';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import CredentialLookup from '../../../../components/Lookup/CredentialLookup';
import {
  GroupByField,
  InstanceFiltersField,
  OptionsField,
  RegionsField,
  SourceVarsField,
  VerbosityField,
} from './SharedFields';

const EC2SubForm = ({ i18n, sourceOptions }) => {
  const [credentialField, , credentialHelpers] = useField('credential');
  const groupByOptionsObj = Object.assign(
    {},
    ...sourceOptions?.actions?.POST?.group_by?.ec2_group_by_choices.map(
      ([key, val]) => ({ [key]: val })
    )
  );

  return (
    <>
      <CredentialLookup
        credentialTypeNamespace="aws"
        label={i18n._(t`Credential`)}
        value={credentialField.value}
        onChange={value => {
          credentialHelpers.setValue(value);
        }}
      />
      <RegionsField
        regionOptions={
          sourceOptions?.actions?.POST?.source_regions?.ec2_region_choices
        }
      />
      <InstanceFiltersField />
      <GroupByField fixedOptions={groupByOptionsObj} />
      <VerbosityField />
      <OptionsField />
      <SourceVarsField />
    </>
  );
};

export default withI18n()(EC2SubForm);
