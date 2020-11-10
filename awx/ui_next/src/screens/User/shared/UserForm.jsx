import React, { useCallback, useState } from 'react';
import PropTypes from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Formik, useField, useFormikContext } from 'formik';
import { Form, FormGroup } from '@patternfly/react-core';
import AnsibleSelect from '../../../components/AnsibleSelect';
import FormActionGroup from '../../../components/FormActionGroup/FormActionGroup';
import FormField, {
  PasswordField,
  FormSubmitError,
} from '../../../components/FormField';
import OrganizationLookup from '../../../components/Lookup/OrganizationLookup';
import { required, requiredEmail } from '../../../util/validators';
import { FormColumnLayout } from '../../../components/FormLayout';

function UserFormFields({ user, i18n }) {
  const [organization, setOrganization] = useState(null);
  const { setFieldValue } = useFormikContext();

  const ldapUser = user.ldap_dn;
  const socialAuthUser = user.auth?.length > 0;
  const externalAccount = user.external_account;

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

  const [, organizationMeta, organizationHelpers] = useField({
    name: 'organization',
    validate: !user.id
      ? required(i18n._(t`Select a value for this field`), i18n)
      : () => undefined,
  });

  const [userTypeField, userTypeMeta] = useField('user_type');

  const onOrganizationChange = useCallback(
    value => {
      setFieldValue('organization', value.id);
      setOrganization(value);
    },
    [setFieldValue]
  );

  return (
    <>
      <FormField
        id="user-username"
        label={i18n._(t`Username`)}
        name="username"
        type="text"
        validate={
          !ldapUser && !externalAccount ? required(null, i18n) : () => undefined
        }
        isRequired={!ldapUser && !externalAccount}
      />
      <FormField
        id="user-email"
        label={i18n._(t`Email`)}
        name="email"
        validate={requiredEmail(i18n)}
        isRequired
      />
      {!ldapUser && !(socialAuthUser && externalAccount) && (
        <>
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
        </>
      )}
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
        <OrganizationLookup
          helperTextInvalid={organizationMeta.error}
          isValid={!organizationMeta.touched || !organizationMeta.error}
          onBlur={() => organizationHelpers.setTouched()}
          onChange={onOrganizationChange}
          value={organization}
          required
          autoPopulate={!user?.id}
        />
      )}
      <FormGroup
        fieldId="user-type"
        helperTextInvalid={userTypeMeta.error}
        isRequired
        validated={
          !userTypeMeta.touched || !userTypeMeta.error ? 'default' : 'error'
        }
        label={i18n._(t`User Type`)}
      >
        <AnsibleSelect
          isValid={!userTypeMeta.touched || !userTypeMeta.error}
          id="user-type"
          data={userTypeOptions}
          {...userTypeField}
        />
      </FormGroup>
    </>
  );
}

function UserForm({ user, handleCancel, handleSubmit, submitError, i18n }) {
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
      const { confirm_password, ...submitValues } = values;
      handleSubmit(submitValues);
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
    >
      {formik => (
        <Form autoComplete="off" onSubmit={formik.handleSubmit}>
          <FormColumnLayout>
            <UserFormFields user={user} i18n={i18n} />
            <FormSubmitError error={submitError} />
            <FormActionGroup
              onCancel={handleCancel}
              onSubmit={formik.handleSubmit}
            />
          </FormColumnLayout>
        </Form>
      )}
    </Formik>
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
