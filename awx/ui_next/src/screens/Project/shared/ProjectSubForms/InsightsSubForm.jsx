import React from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { useField } from 'formik';
import CredentialLookup from '@components/Lookup/CredentialLookup';
import { required } from '@util/validators';
import { ScmTypeOptions } from './SharedFields';

const InsightsSubForm = ({
  i18n,
  credential,
  onCredentialSelection,
  scmUpdateOnLaunch,
}) => {
  const credFieldArr = useField({
    name: 'credential',
    validate: required(i18n._(t`Select a value for this field`), i18n),
  });
  const credMeta = credFieldArr[1];
  const credHelpers = credFieldArr[2];

  return (
    <>
      <CredentialLookup
        credentialTypeId={credential.typeId}
        label={i18n._(t`Insights Credential`)}
        helperTextInvalid={credMeta.error}
        isValid={!credMeta.touched || !credMeta.error}
        onBlur={() => credHelpers.setTouched()}
        onChange={value => {
          onCredentialSelection('insights', value);
          credHelpers.setValue(value.id);
        }}
        value={credential.value}
        required
      />
      <ScmTypeOptions hideAllowOverride scmUpdateOnLaunch={scmUpdateOnLaunch} />
    </>
  );
};

export default withI18n()(InsightsSubForm);
