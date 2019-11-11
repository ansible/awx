import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Formik, Field } from 'formik';
import { Form, FormGroup } from '@patternfly/react-core';
import AnsibleSelect from '@components/AnsibleSelect';
import FormActionGroup from '@components/FormActionGroup/FormActionGroup';
import FormField, { PasswordField } from '@components/FormField';
import FormRow from '@components/FormRow';
import OrganizationLookup from '@components/Lookup/OrganizationLookup';
import { required, requiredEmail } from '@util/validators';

function UserForm(props) {
  const { user, handleCancel, handleSubmit, i18n } = props;
  const [organization, setOrganization] = useState(null);

  const userTypeOptions = [
    {
      value: 'normal',
      key: 'normal',
      label: i18n._(t`Normal User`),
      isDisabled: false,
    },
    {
      value: 'auditor',
      key: 'auditor',
      label: i18n._(t`System Auditor`),
      isDisabled: false,
    },
    {
      value: 'administrator',
      key: 'administrator',
      label: i18n._(t`System Administrator`),
      isDisabled: false,
    },
  ];

  const handleValidateAndSubmit = (values, { setErrors }) => {
    if (values.password !== values.confirm_password) {
      setErrors({
        confirm_password: i18n._(
          t`This value does not match the password you entered previously. Please confirm that password.`
        ),
      });
    } else {
      values.is_superuser = values.user_type === 'administrator';
      values.is_system_auditor = values.user_type === 'auditor';
      if (!values.password || values.password === '') {
        delete values.password;
      }
      delete values.confirm_password;
      handleSubmit(values);
    }
  };

  let userType;
  if (user.is_superuser) {
    userType = 'administrator';
  } else if (user.is_system_auditor) {
    userType = 'auditor';
  } else {
    userType = 'normal';
  }

  return (
    <Formik
      initialValues={{
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        organization: user.organization || '',
        email: user.email || '',
        username: user.username || '',
        password: '',
        confirm_password: '',
        user_type: userType,
      }}
      onSubmit={handleValidateAndSubmit}
      render={formik => (
        <Form
          autoComplete="off"
          onSubmit={formik.handleSubmit}
          css="padding: 0 24px"
        >
          <FormRow>
            <FormField
              id="user-username"
              label={i18n._(t`Username`)}
              name="username"
              type="text"
              validate={required(null, i18n)}
              isRequired
            />
            <FormField
              id="user-email"
              label={i18n._(t`Email`)}
              name="email"
              validate={requiredEmail(i18n)}
              isRequired
            />
            <PasswordField
              id="user-password"
              label={i18n._(t`Password`)}
              name="password"
              validate={
                !user.id
                  ? required(i18n._(t`This field must not be blank`), i18n)
                  : () => undefined
              }
              isRequired={!user.id}
            />
            <PasswordField
              id="user-confirm-password"
              label={i18n._(t`Confirm Password`)}
              name="confirm_password"
              validate={
                !user.id
                  ? required(i18n._(t`This field must not be blank`), i18n)
                  : () => undefined
              }
              isRequired={!user.id}
            />
          </FormRow>
          <FormRow>
            <FormField
              id="user-first-name"
              label={i18n._(t`First Name`)}
              name="first_name"
              type="text"
            />
            <FormField
              id="user-last-name"
              label={i18n._(t`Last Name`)}
              name="last_name"
              type="text"
            />
            {!user.id && (
              <Field
                name="organization"
                validate={required(
                  i18n._(t`Select a value for this field`),
                  i18n
                )}
                render={({ form }) => (
                  <OrganizationLookup
                    helperTextInvalid={form.errors.organization}
                    isValid={
                      !form.touched.organization || !form.errors.organization
                    }
                    onBlur={() => form.setFieldTouched('organization')}
                    onChange={value => {
                      form.setFieldValue('organization', value.id);
                      setOrganization(value);
                    }}
                    value={organization}
                    required
                  />
                )}
              />
            )}
            <Field
              name="user_type"
              render={({ form, field }) => {
                const isValid =
                  !form.touched.user_type || !form.errors.user_type;
                return (
                  <FormGroup
                    fieldId="user-type"
                    helperTextInvalid={form.errors.user_type}
                    isRequired
                    isValid={isValid}
                    label={i18n._(t`User Type`)}
                  >
                    <AnsibleSelect
                      isValid={isValid}
                      id="user-type"
                      data={userTypeOptions}
                      {...field}
                    />
                  </FormGroup>
                );
              }}
            />
          </FormRow>
          <FormActionGroup
            onCancel={handleCancel}
            onSubmit={formik.handleSubmit}
          />
        </Form>
      )}
    />
  );
}

UserForm.propTypes = {
  handleCancel: PropTypes.func.isRequired,
  handleSubmit: PropTypes.func.isRequired,
  user: PropTypes.shape({}),
};

UserForm.defaultProps = {
  user: {},
};

export default withI18n()(UserForm);
