import React, { useCallback } from 'react';
import { func, shape } from 'prop-types';
import { Formik, useField, useFormikContext } from 'formik';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Form } from '@patternfly/react-core';

import CredentialLookup from '../../../components/Lookup/CredentialLookup';
import FormActionGroup from '../../../components/FormActionGroup';
import FormField, { FormSubmitError } from '../../../components/FormField';
import { FormColumnLayout } from '../../../components/FormLayout';
import { OrganizationLookup } from '../../../components/Lookup';
import { required, url } from '../../../util/validators';

function ExecutionEnvironmentFormFields({ i18n, me, executionEnvironment }) {
  const [credentialField] = useField('credential');
  const [organizationField, organizationMeta, organizationHelpers] = useField({
    name: 'organization',
    validate:
      !me?.is_superuser &&
      required(i18n._(t`Select a value for this field`), i18n),
  });

  const { setFieldValue } = useFormikContext();

  const onCredentialChange = useCallback(
    value => {
      setFieldValue('credential', value);
    },
    [setFieldValue]
  );

  const onOrganizationChange = useCallback(
    value => {
      setFieldValue('organization', value);
    },
    [setFieldValue]
  );

  return (
    <>
      <FormField
        id="execution-environment-image"
        label={i18n._(t`Image name`)}
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
      <OrganizationLookup
        helperTextInvalid={organizationMeta.error}
        isValid={!organizationMeta.touched || !organizationMeta.error}
        onBlur={() => organizationHelpers.setTouched()}
        onChange={onOrganizationChange}
        value={organizationField.value}
        required={!me.is_superuser}
        helperText={
          me?.is_superuser
            ? i18n._(
                t`Leave this field blank to make the execution environment globally available.`
              )
            : null
        }
        autoPopulate={!me?.is_superuser ? !executionEnvironment?.id : null}
      />

      <CredentialLookup
        label={i18n._(t`Registry credential`)}
        onChange={onCredentialChange}
        value={credentialField.value}
      />
    </>
  );
}

function ExecutionEnvironmentForm({
  executionEnvironment = {},
  onSubmit,
  onCancel,
  submitError,
  me,
  ...rest
}) {
  const initialValues = {
    image: executionEnvironment.image || '',
    description: executionEnvironment.description || '',
    credential: executionEnvironment.summary_fields?.credential || null,
    organization: executionEnvironment.summary_fields?.organization || null,
  };
  return (
    <Formik initialValues={initialValues} onSubmit={values => onSubmit(values)}>
      {formik => (
        <Form autoComplete="off" onSubmit={formik.handleSubmit}>
          <FormColumnLayout>
            <ExecutionEnvironmentFormFields me={me} {...rest} />
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
