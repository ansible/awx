import React from 'react';
import { func, shape } from 'prop-types';
import { Formik, useField } from 'formik';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import { Form } from '@patternfly/react-core';
import FormField, { FormSubmitError } from '../../../components/FormField';
import FormActionGroup from '../../../components/FormActionGroup';
import CredentialLookup from '../../../components/Lookup/CredentialLookup';
import { url } from '../../../util/validators';
import { FormColumnLayout } from '../../../components/FormLayout';

function ExecutionEnvironmentFormFields({ i18n }) {
  const [credentialField, , credentialHelpers] = useField('credential');
  return (
    <>
      <FormField
        id="execution-environment-image"
        label={i18n._(t`Image`)}
        name="image"
        type="text"
        validate={url(i18n)}
        isRequired
        tooltip={i18n._(
          t`The registry location where the container is stored.`
        )}
      />
      <FormField
        id="execution-environment-description"
        label={i18n._(t`Description`)}
        name="description"
        type="text"
      />
      <CredentialLookup
        label={i18n._(t`Registry Credential`)}
        onChange={value => credentialHelpers.setValue(value)}
        value={credentialField.value || null}
      />
    </>
  );
}

function ExecutionEnvironmentForm({
  executionEnvironment = {},
  onSubmit,
  onCancel,
  submitError,
  ...rest
}) {
  const initialValues = {
    image: executionEnvironment.image || '',
    description: executionEnvironment.description || '',
    credential: executionEnvironment?.summary_fields?.credential || null,
  };
  return (
    <Formik initialValues={initialValues} onSubmit={values => onSubmit(values)}>
      {formik => (
        <Form autoComplete="off" onSubmit={formik.handleSubmit}>
          <FormColumnLayout>
            <ExecutionEnvironmentFormFields {...rest} />
            {submitError && <FormSubmitError error={submitError} />}
            <FormActionGroup
              onCancel={onCancel}
              onSubmit={formik.handleSubmit}
            />
          </FormColumnLayout>
        </Form>
      )}
    </Formik>
  );
}

ExecutionEnvironmentForm.propTypes = {
  executionEnvironment: shape({}),
  onCancel: func.isRequired,
  onSubmit: func.isRequired,
  submitError: shape({}),
};

ExecutionEnvironmentForm.defaultProps = {
  executionEnvironment: {},
  submitError: null,
};

export default withI18n()(ExecutionEnvironmentForm);
