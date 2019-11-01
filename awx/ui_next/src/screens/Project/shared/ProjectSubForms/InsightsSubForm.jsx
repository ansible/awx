import React from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Field } from 'formik';
import CredentialLookup from '@components/Lookup/CredentialLookup';
import { required } from '@util/validators';
import { ScmTypeOptions } from './SharedFields';

const InsightsSubForm = ({
  i18n,
  setInsightsCredential,
  insightsCredential,
  scmUpdateOnLaunch,
}) => (
  <>
    <Field
      name="credential"
      validate={required(i18n._(t`Select a value for this field`), i18n)}
      render={({ form }) => (
        <CredentialLookup
          credentialTypeId={insightsCredential.typeId}
          label={i18n._(t`Insights Credential`)}
          helperTextInvalid={form.errors.credential}
          isValid={!form.touched.credential || !form.errors.credential}
          onBlur={() => form.setFieldTouched('credential')}
          onChange={credential => {
            form.setFieldValue('credential', credential.id);
            setInsightsCredential({
              ...insightsCredential,
              value: credential,
            });
          }}
          value={insightsCredential.value}
          required
        />
      )}
    />
    <ScmTypeOptions hideAllowOverride scmUpdateOnLaunch={scmUpdateOnLaunch} />
  </>
);

export default withI18n()(InsightsSubForm);
