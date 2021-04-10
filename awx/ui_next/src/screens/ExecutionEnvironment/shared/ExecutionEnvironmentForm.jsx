import React, { useCallback, useEffect, useRef } from 'react';
import { func, shape, bool } from 'prop-types';
import { Formik, useField, useFormikContext } from 'formik';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Form, FormGroup, Tooltip } from '@patternfly/react-core';

import { ExecutionEnvironmentsAPI } from '../../../api';
import CredentialLookup from '../../../components/Lookup/CredentialLookup';
import FormActionGroup from '../../../components/FormActionGroup';
import FormField, { FormSubmitError } from '../../../components/FormField';
import AnsibleSelect from '../../../components/AnsibleSelect';
import { FormColumnLayout } from '../../../components/FormLayout';
import { OrganizationLookup } from '../../../components/Lookup';
import ContentError from '../../../components/ContentError';
import ContentLoading from '../../../components/ContentLoading';
import { required } from '../../../util/validators';
import useRequest from '../../../util/useRequest';

function ExecutionEnvironmentFormFields({
  i18n,
  me,
  options,
  executionEnvironment,
  isOrgLookupDisabled,
}) {
  const [credentialField, credentialMeta, credentialHelpers] = useField(
    'credential'
  );
  const [organizationField, organizationMeta, organizationHelpers] = useField({
    name: 'organization',
    validate:
      !me?.is_superuser &&
      required(i18n._(t`Select a value for this field`), i18n),
  });

  const isGloballyAvailable = useRef(!organizationField.value);

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
    name: 'pull',
  });

  const containerPullChoices = options?.actions?.POST?.pull?.choices.map(
    ([value, label]) => ({ value, label, key: value })
  );

  const renderOrganizationLookup = () => {
    return (
      <OrganizationLookup
        helperTextInvalid={organizationMeta.error}
        isValid={!organizationMeta.touched || !organizationMeta.error}
        onBlur={() => organizationHelpers.setTouched()}
        onChange={onOrganizationChange}
        value={organizationField.value}
        required={!me.is_superuser}
        helperText={
          me?.is_superuser &&
          ((!isOrgLookupDisabled && isGloballyAvailable) ||
            organizationField.value === null)
            ? i18n._(
                t`Leave this field blank to make the execution environment globally available.`
              )
            : null
        }
        autoPopulate={!me?.is_superuser ? !executionEnvironment?.id : null}
        isDisabled={!!isOrgLookupDisabled && isGloballyAvailable.current}
      />
    );
  };

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
        validate={required(null, i18n)}
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
        label={i18n._(t`Pull`)}
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
      {isOrgLookupDisabled && isGloballyAvailable.current ? (
        <Tooltip
          content={i18n._(
            t`Globally available execution environment can not be reassigned to a specific Organization`
          )}
        >
          {renderOrganizationLookup()}
        </Tooltip>
      ) : (
        renderOrganizationLookup()
      )}

      <CredentialLookup
        label={i18n._(t`Registry credential`)}
        credentialTypeKind="registry"
        helperTextInvalid={credentialMeta.error}
        isValid={!credentialMeta.touched || !credentialMeta.error}
        onBlur={() => credentialHelpers.setTouched()}
        onChange={onCredentialChange}
        value={credentialField.value}
        tooltip={i18n._(
          t`Credential to authenticate with a protected container registry.`
        )}
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
  isOrgLookupDisabled,
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
    pull: executionEnvironment?.pull || '',
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
              isOrgLookupDisabled={isOrgLookupDisabled}
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
  isOrgLookupDisabled: bool,
};

ExecutionEnvironmentForm.defaultProps = {
  executionEnvironment: {},
  submitError: null,
  isOrgLookupDisabled: false,
};

export default withI18n()(ExecutionEnvironmentForm);
