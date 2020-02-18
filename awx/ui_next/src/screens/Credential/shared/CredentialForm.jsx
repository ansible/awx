import React from 'react';
import { Formik, useField } from 'formik';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { func, shape } from 'prop-types';
import { Form, FormGroup, Title } from '@patternfly/react-core';
import FormField from '@components/FormField';
import FormActionGroup from '@components/FormActionGroup/FormActionGroup';
import AnsibleSelect from '@components/AnsibleSelect';
import { required } from '@util/validators';
import OrganizationLookup from '@components/Lookup/OrganizationLookup';
import { FormColumnLayout, SubFormLayout } from '@components/FormLayout';
import { ManualSubForm, SourceControlSubForm } from './CredentialSubForms';

function CredentialFormFields({
  i18n,
  credentialTypes,
  formik,
  initialValues,
}) {
  const [orgField, orgMeta, orgHelpers] = useField('organization');
  const [credTypeField, credTypeMeta, credTypeHelpers] = useField({
    name: 'credential_type',
    validate: required(i18n._(t`Select a value for this field`), i18n),
  });

  const credentialTypeOptions = Object.keys(credentialTypes).map(key => {
    return {
      value: credentialTypes[key].id,
      key: credentialTypes[key].kind,
      label: credentialTypes[key].name,
    };
  });
  const scmCredentialTypeId = Object.keys(credentialTypes)
    .filter(key => credentialTypes[key].kind === 'scm')
    .map(key => credentialTypes[key].id)[0];
  const sshCredentialTypeId = Object.keys(credentialTypes)
    .filter(key => credentialTypes[key].kind === 'ssh')
    .map(key => credentialTypes[key].id)[0];

  const resetSubFormFields = (value, form) => {
    Object.keys(form.initialValues.inputs).forEach(label => {
      if (parseInt(value, 10) === form.initialValues.credential_type) {
        form.setFieldValue(`inputs.${label}`, initialValues.inputs[label]);
      } else {
        form.setFieldValue(`inputs.${label}`, undefined);
      }
      form.setFieldTouched(`inputs.${label}`, false);
    });
  };

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
            credTypeHelpers.setValue(value);
            resetSubFormFields(value, formik);
          }}
        />
      </FormGroup>
      {formik.values.credential_type !== undefined &&
        formik.values.credential_type !== '' && (
          <SubFormLayout>
            <Title size="md">{i18n._(t`Type Details`)}</Title>
            {
              {
                [sshCredentialTypeId]: <ManualSubForm />,
                [scmCredentialTypeId]: <SourceControlSubForm />,
              }[formik.values.credential_type]
            }
          </SubFormLayout>
        )}
    </>
  );
}

function CredentialForm({ credential = {}, onSubmit, onCancel, ...rest }) {
  const initialValues = {
    name: credential.name || undefined,
    description: credential.description || undefined,
    organization:
      (credential.summary_fields && credential.summary_fields.organization) ||
      null,
    credential_type: credential.credential_type || undefined,
    inputs: {
      username: (credential.inputs && credential.inputs.username) || undefined,
      password: (credential.inputs && credential.inputs.password) || undefined,
      ssh_key_data:
        (credential.inputs && credential.inputs.ssh_key_data) || undefined,
      ssh_public_key_data:
        (credential.inputs && credential.inputs.ssh_public_key_data) ||
        undefined,
      ssh_key_unlock:
        (credential.inputs && credential.inputs.ssh_key_unlock) || undefined,
      become_method:
        (credential.inputs && credential.inputs.become_method) || undefined,
      become_username:
        (credential.inputs && credential.inputs.become_username) || undefined,
      become_password:
        (credential.inputs && credential.inputs.become_password) || undefined,
    },
  };

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
              initialValues={initialValues}
              {...rest}
            />
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
  credential: shape({}),
};

CredentialForm.defaultProps = {
  credential: {},
};

export default withI18n()(CredentialForm);
