import React, { useCallback } from 'react';

import { t } from '@lingui/macro';
import { useField, useFormikContext } from 'formik';
import CredentialLookup from '../../../../components/Lookup/CredentialLookup';
import { required } from '../../../../util/validators';
import { ScmTypeOptions } from './SharedFields';

const InsightsSubForm = ({
  credential,
  onCredentialSelection,
  scmUpdateOnLaunch,
  autoPopulateCredential,
}) => {
  const { setFieldValue } = useFormikContext();
  const [, credMeta, credHelpers] = useField({
    name: 'credential',
    validate: required(t`Select a value for this field`),
  });

  const onCredentialChange = useCallback(
    value => {
      onCredentialSelection('insights', value);
      setFieldValue('credential', value.id);
    },
    [onCredentialSelection, setFieldValue]
  );

  return (
    <>
      <CredentialLookup
        credentialTypeId={credential.typeId}
        label={t`Insights Credential`}
        helperTextInvalid={credMeta.error}
        isValid={!credMeta.touched || !credMeta.error}
        onBlur={() => credHelpers.setTouched()}
        onChange={onCredentialChange}
        value={credential.value}
        required
        autoPopulate={autoPopulateCredential}
      />
      <ScmTypeOptions hideAllowOverride scmUpdateOnLaunch={scmUpdateOnLaunch} />
    </>
  );
};

export default InsightsSubForm;
