import React from 'react';
import { Formik, useField } from 'formik';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { func, shape } from 'prop-types';
import { Form, FormGroup, Title } from '@patternfly/react-core';
import FormField, { FormSubmitError } from '@components/FormField';
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
  scmCredentialTypeId,
  sshCredentialTypeId,
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

  const resetSubFormFields = (value, form) => {
    Object.keys(form.initialValues.inputs).forEach(label => {
      if (parseInt(value, 10) === form.initialValues.credential_type) {
        form.setFieldValue(`inputs.${label}`, initialValues.inputs[label]);
      } else {
        form.setFieldValue(`inputs.${label}`, '');
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

function CredentialForm({
  credential = {},
  credentialTypes,
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
    inputs: {
      username: credential?.inputs?.username || '',
      password: credential?.inputs?.password || '',
      ssh_key_data: credential?.inputs?.ssh_key_data || '',
      ssh_public_key_data: credential?.inputs?.ssh_public_key_data || '',
      ssh_key_unlock: credential?.inputs?.ssh_key_unlock || '',
      become_method: credential?.inputs?.become_method || '',
      become_username: credential?.inputs?.become_username || '',
      become_password: credential?.inputs?.become_password || '',
    },
  };

  const scmCredentialTypeId = Object.keys(credentialTypes)
    .filter(key => credentialTypes[key].kind === 'scm')
    .map(key => credentialTypes[key].id)[0];
  const sshCredentialTypeId = Object.keys(credentialTypes)
    .filter(key => credentialTypes[key].kind === 'ssh')
    .map(key => credentialTypes[key].id)[0];

  return (
    <Formik
      initialValues={initialValues}
      onSubmit={values => {
        const scmKeys = [
          'username',
          'password',
          'ssh_key_data',
          'ssh_key_unlock',
        ];
        const sshKeys = [
          'username',
          'password',
          'ssh_key_data',
          'ssh_public_key_data',
          'ssh_key_unlock',
          'become_method',
          'become_username',
          'become_password',
        ];
        if (parseInt(values.credential_type, 10) === scmCredentialTypeId) {
          Object.keys(values.inputs).forEach(key => {
            if (scmKeys.indexOf(key) < 0) {
              delete values.inputs[key];
            }
          });
        } else if (
          parseInt(values.credential_type, 10) === sshCredentialTypeId
        ) {
          Object.keys(values.inputs).forEach(key => {
            if (sshKeys.indexOf(key) < 0) {
              delete values.inputs[key];
            }
          });
        }
        onSubmit(values);
      }}
    >
      {formik => (
        <Form autoComplete="off" onSubmit={formik.handleSubmit}>
          <FormColumnLayout>
            <CredentialFormFields
              formik={formik}
              initialValues={initialValues}
              credentialTypes={credentialTypes}
              scmCredentialTypeId={scmCredentialTypeId}
              sshCredentialTypeId={sshCredentialTypeId}
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
  credential: shape({}),
};

CredentialForm.defaultProps = {
  credential: {},
};

export default withI18n()(CredentialForm);
