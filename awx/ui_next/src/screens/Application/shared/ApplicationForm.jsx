import React, { useCallback } from 'react';
import { useRouteMatch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Formik, useField, useFormikContext } from 'formik';
import { Form, FormGroup } from '@patternfly/react-core';
import PropTypes from 'prop-types';

import { required } from '../../../util/validators';
import FormField, { FormSubmitError } from '../../../components/FormField';
import { FormColumnLayout } from '../../../components/FormLayout';
import FormActionGroup from '../../../components/FormActionGroup/FormActionGroup';
import OrganizationLookup from '../../../components/Lookup/OrganizationLookup';
import AnsibleSelect from '../../../components/AnsibleSelect';
import Popover from '../../../components/Popover';

function ApplicationFormFields({
  i18n,
  application,
  authorizationOptions,
  clientTypeOptions,
}) {
  const match = useRouteMatch();
  const { setFieldValue } = useFormikContext();
  const [organizationField, organizationMeta, organizationHelpers] = useField({
    name: 'organization',
    validate: required(null, i18n),
  });
  const [
    authorizationTypeField,
    authorizationTypeMeta,
    authorizationTypeHelpers,
  ] = useField({
    name: 'authorization_grant_type',
    validate: required(null, i18n),
  });

  const [clientTypeField, clientTypeMeta, clientTypeHelpers] = useField({
    name: 'client_type',
    validate: required(null, i18n),
  });

  const onOrganizationChange = useCallback(
    value => {
      setFieldValue('organization', value);
    },
    [setFieldValue]
  );

  return (
    <>
      <FormField
        id="name"
        label={i18n._(t`Name`)}
        name="name"
        type="text"
        validate={required(null, i18n)}
        isRequired
      />
      <FormField
        id="description"
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
        required
        autoPopulate={!application?.id}
      />
      <FormGroup
        fieldId="authType"
        helperTextInvalid={authorizationTypeMeta.error}
        validated={
          !authorizationTypeMeta.touched || !authorizationTypeMeta.error
            ? 'default'
            : 'error'
        }
        isRequired
        label={i18n._(t`Authorization grant type`)}
        labelIcon={
          <Popover
            content={i18n._(
              t`The Grant type the user must use for acquire tokens for this application`
            )}
          />
        }
      >
        <AnsibleSelect
          {...authorizationTypeField}
          isValid={
            !authorizationTypeMeta.touched || !authorizationTypeMeta.error
          }
          isDisabled={match.url.endsWith('edit')}
          id="authType"
          data={[{ label: '', key: 1, value: '' }, ...authorizationOptions]}
          onChange={(event, value) => {
            authorizationTypeHelpers.setValue(value);
          }}
        />
      </FormGroup>
      <FormField
        id="redirect_uris"
        label={i18n._(t`Redirect URIs`)}
        name="redirect_uris"
        type="text"
        isRequired={Boolean(
          authorizationTypeField.value === 'authorization-code'
        )}
        validate={
          authorizationTypeField.value === 'authorization-code'
            ? required(null, i18n)
            : null
        }
        tooltip={i18n._(t`Allowed URIs list, space separated`)}
      />
      <FormGroup
        fieldId="clientType"
        helperTextInvalid={clientTypeMeta.error}
        validated={
          !clientTypeMeta.touched || !clientTypeMeta.error ? 'default' : 'error'
        }
        isRequired
        label={i18n._(t`Client type`)}
        labelIcon={
          <Popover
            content={i18n._(
              t`Set to Public or Confidential depending on how secure the client device is.`
            )}
          />
        }
      >
        <AnsibleSelect
          {...clientTypeField}
          isValid={!clientTypeMeta.touched || !clientTypeMeta.error}
          id="clientType"
          data={[{ label: '', key: 1, value: '' }, ...clientTypeOptions]}
          onChange={(event, value) => {
            clientTypeHelpers.setValue(value);
          }}
        />
      </FormGroup>
    </>
  );
}
function ApplicationForm({
  onCancel,
  onSubmit,
  i18n,
  submitError,
  application,
  authorizationOptions,
  clientTypeOptions,
}) {
  const initialValues = {
    name: application?.name || '',
    description: application?.description || '',
    organization: application?.summary_fields?.organization || null,
    authorization_grant_type: application?.authorization_grant_type || '',
    redirect_uris: application?.redirect_uris || '',
    client_type: application?.client_type || '',
  };

  return (
    <Formik initialValues={initialValues} onSubmit={values => onSubmit(values)}>
      {formik => (
        <Form autoComplete="off" onSubmit={formik.handleSubmit}>
          <FormColumnLayout>
            <ApplicationFormFields
              formik={formik}
              application={application}
              authorizationOptions={authorizationOptions}
              clientTypeOptions={clientTypeOptions}
              i18n={i18n}
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

ApplicationForm.propTypes = {
  onSubmit: PropTypes.func.isRequired,
  onCancel: PropTypes.func.isRequired,
  authorizationOptions: PropTypes.arrayOf(PropTypes.object).isRequired,
  clientTypeOptions: PropTypes.arrayOf(PropTypes.object).isRequired,
};

export default withI18n()(ApplicationForm);
