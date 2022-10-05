import React, { useCallback } from 'react';

import { t } from '@lingui/macro';
import { useFormikContext, useField } from 'formik';
import CredentialLookup from 'components/Lookup/CredentialLookup';
import { required } from 'util/validators';
import { ScmTypeOptions } from './SharedFields';

const InsightsSubForm = ({
  credentialTypeId,
  scmUpdateOnLaunch,
  autoPopulateCredential,
}) => {
  const { setFieldValue, setFieldTouched } = useFormikContext();
  const [credField, credMeta, credHelpers] = useField('credential');

  const onCredentialChange = useCallback(
    (value) => {
      setFieldValue('credential', value);
      setFieldTouched('credential', true, false);
    },
    [setFieldValue, setFieldTouched]
  );

  return (
    <>
      <CredentialLookup
        credentialTypeId={credentialTypeId}
        label={t`Insights Credential`}
        helperTextInvalid={credMeta.error}
        isValid={!credMeta.touched || !credMeta.error}
        onBlur={() => credHelpers.setTouched()}
        onChange={onCredentialChange}
        value={credField.value}
        required
        autoPopulate={autoPopulateCredential}
        validate={required(t`Select a value for this field`)}
      />
      <ScmTypeOptions hideAllowOverride scmUpdateOnLaunch={scmUpdateOnLaunch} />
    </>
  );
};

export default InsightsSubForm;
