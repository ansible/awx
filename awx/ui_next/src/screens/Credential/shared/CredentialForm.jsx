import React from 'react';
import { Formik, useField } from 'formik';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { arrayOf, func, object, shape } from 'prop-types';
import { Form, FormGroup } from '@patternfly/react-core';
import FormField, { FormSubmitError } from '../../../components/FormField';
import FormActionGroup from '../../../components/FormActionGroup/FormActionGroup';
import AnsibleSelect from '../../../components/AnsibleSelect';
import { required } from '../../../util/validators';
import OrganizationLookup from '../../../components/Lookup/OrganizationLookup';
import { FormColumnLayout } from '../../../components/FormLayout';
import TypeInputsSubForm from './TypeInputsSubForm';

function CredentialFormFields({ i18n, credentialTypes, formik }) {
  const [orgField, orgMeta, orgHelpers] = useField('organization');
  const [credTypeField, credTypeMeta] = useField({
    name: 'credential_type',
    validate: required(i18n._(t`Select a value for this field`), i18n),
  });

  const credentialTypeOptions = Object.keys(credentialTypes)
    .map(key => {
      return {
        value: credentialTypes[key].id,
        key: credentialTypes[key].id,
        label: credentialTypes[key].name,
      };
    })
    .sort((a, b) => (a.label.toLowerCase() > b.label.toLowerCase() ? 1 : -1));

  return (
    <>
      <FormField
        id="credential-name"
        label={i18n._(t`Name`)}
        name="name"
        type="text"
        validate={required(null, i18n)}
        isRequired
      />
      <FormField
        id="credential-description"
        label={i18n._(t`Description`)}
        name="description"
        type="text"
      />
      <OrganizationLookup
        helperTextInvalid={orgMeta.error}
        isValid={!orgMeta.touched || !orgMeta.error}
        onBlur={() => orgHelpers.setTouched()}
        onChange={value => {
          orgHelpers.setValue(value);
        }}
        value={orgField.value}
        touched={orgMeta.touched}
        error={orgMeta.error}
      />
      <FormGroup
        fieldId="credential-credentialType"
        helperTextInvalid={credTypeMeta.error}
        isRequired
        isValid={!credTypeMeta.touched || !credTypeMeta.error}
        label={i18n._(t`Credential Type`)}
      >
        <AnsibleSelect
          {...credTypeField}
          id="credential_type"
          data={[
            {
              value: '',
              key: '',
              label: i18n._(t`Choose a Credential Type`),
              isDisabled: true,
            },
            ...credentialTypeOptions,
          ]}
          onChange={(event, value) => {
            const { values, initialValues, resetForm } = formik;
            resetForm({
              values: {
                ...initialValues,
                name: values.name,
                description: values.description,
                organization: values.organization,
                credential_type: value,
              },
            });
          }}
        />
      </FormGroup>
      {credTypeField.value !== undefined &&
        credTypeField.value !== '' &&
        credentialTypes[credTypeField.value]?.inputs?.fields && (
          <TypeInputsSubForm
            credentialType={credentialTypes[credTypeField.value]}
          />
        )}
    </>
  );
}

function CredentialForm({
  credential = {},
  credentialTypes,
  inputSources,
  onSubmit,
  onCancel,
  submitError,
  ...rest
}) {
  const initialValues = {
    name: credential.name || '',
    description: credential.description || '',
    organization: credential?.summary_fields?.organization || null,
    credential_type: credential.credential_type || '',
    inputs: {},
    passwordPrompts: {},
  };

  Object.values(credentialTypes).forEach(credentialType => {
    const fields = credentialType.inputs.fields || [];
    fields.forEach(
      ({ ask_at_runtime, type, id, choices, default: defaultValue }) => {
        if (credential?.inputs && credential.inputs[id]) {
          if (ask_at_runtime) {
            initialValues.passwordPrompts[id] =
              credential.inputs[id] === 'ASK' || false;
          }
          initialValues.inputs[id] = credential.inputs[id];
        } else {
          switch (type) {
            case 'string':
              initialValues.inputs[id] = defaultValue || '';
              break;
            case 'boolean':
              initialValues.inputs[id] = defaultValue || false;
              break;
            default:
              break;
          }

          if (choices) {
            initialValues.inputs[id] = defaultValue;
          }

          if (ask_at_runtime) {
            initialValues.passwordPrompts[id] = false;
          }
        }
      }
    );
  });

  Object.values(inputSources).forEach(inputSource => {
    initialValues.inputs[inputSource.input_field_name] = {
      credential: inputSource.summary_fields.source_credential,
      inputs: inputSource.metadata,
    };
  });

  return (
    <Formik
      initialValues={initialValues}
      onSubmit={values => {
        onSubmit(values);
      }}
    >
      {formik => (
        <Form autoComplete="off" onSubmit={formik.handleSubmit}>
          <FormColumnLayout>
            <CredentialFormFields
              formik={formik}
              credentialTypes={credentialTypes}
              {...rest}
            />
            <FormSubmitError error={submitError} />
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

CredentialForm.proptype = {
  handleSubmit: func.isRequired,
  handleCancel: func.isRequired,
  credentialTypes: shape({}).isRequired,
  credential: shape({}),
  inputSources: arrayOf(object),
  submitError: shape({}),
};

CredentialForm.defaultProps = {
  credential: {},
  inputSources: [],
  submitError: null,
};

export default withI18n()(CredentialForm);
