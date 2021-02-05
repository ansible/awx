import React, { useCallback, useEffect } from 'react';
import { func, shape } from 'prop-types';
import { Formik, useField, useFormikContext } from 'formik';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Form, FormGroup } from '@patternfly/react-core';

import { ExecutionEnvironmentsAPI } from '../../../api';
import CredentialLookup from '../../../components/Lookup/CredentialLookup';
import FormActionGroup from '../../../components/FormActionGroup';
import FormField, { FormSubmitError } from '../../../components/FormField';
import AnsibleSelect from '../../../components/AnsibleSelect';
import { FormColumnLayout } from '../../../components/FormLayout';
import { OrganizationLookup } from '../../../components/Lookup';
import ContentError from '../../../components/ContentError';
import ContentLoading from '../../../components/ContentLoading';
import { required, url } from '../../../util/validators';
import useRequest from '../../../util/useRequest';

function ExecutionEnvironmentFormFields({
  i18n,
  me,
  options,
  executionEnvironment,
}) {
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

  const [
    containerOptionsField,
    containerOptionsMeta,
    containerOptionsHelpers,
  ] = useField({
    name: 'container_options',
  });

  const containerPullChoices = options?.actions?.POST?.container_options?.choices.map(
    ([value, label]) => ({ value, label, key: value })
  );

  return (
    <>
      <FormField
        id="execution-environment-name"
        label={i18n._(t`Name`)}
        name="name"
        type="text"
        validate={required(null, i18n)}
        isRequired
      />
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
      <FormGroup
        fieldId="execution-environment-container-options"
        helperTextInvalid={containerOptionsMeta.error}
        validated={
          !containerOptionsMeta.touched || !containerOptionsMeta.error
            ? 'default'
            : 'error'
        }
        label={i18n._(t`Container Pull Option`)}
      >
        <AnsibleSelect
          {...containerOptionsField}
          id="container-pull-options"
          data={containerPullChoices}
          onChange={(event, value) => {
            containerOptionsHelpers.setValue(value);
          }}
        />
      </FormGroup>
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
  const {
    isLoading,
    error,
    request: fetchOptions,
    result: options,
  } = useRequest(
    useCallback(async () => {
      const res = await ExecutionEnvironmentsAPI.readOptions();
      const { data } = res;
      return data;
    }, []),
    null
  );

  useEffect(() => {
    fetchOptions();
  }, [fetchOptions]);

  if (isLoading || !options) {
    return <ContentLoading />;
  }

  if (error) {
    return <ContentError error={error} />;
  }

  const initialValues = {
    name: executionEnvironment.name || '',
    image: executionEnvironment.image || '',
    container_options: executionEnvironment?.container_options || '',
    description: executionEnvironment.description || '',
    credential: executionEnvironment.summary_fields?.credential || null,
    organization: executionEnvironment.summary_fields?.organization || null,
  };
  return (
    <Formik initialValues={initialValues} onSubmit={values => onSubmit(values)}>
      {formik => (
        <Form autoComplete="off" onSubmit={formik.handleSubmit}>
          <FormColumnLayout>
            <ExecutionEnvironmentFormFields
              me={me}
              options={options}
              executionEnvironment={executionEnvironment}
              {...rest}
            />
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
