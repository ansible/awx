import React from 'react';

import { t } from '@lingui/macro';
import { Formik, useField } from 'formik';
import { Form, FormGroup } from '@patternfly/react-core';
import AnsibleSelect from '../../../components/AnsibleSelect';
import FormActionGroup from '../../../components/FormActionGroup/FormActionGroup';
import FormField, { FormSubmitError } from '../../../components/FormField';
import ApplicationLookup from '../../../components/Lookup/ApplicationLookup';
import Popover from '../../../components/Popover';
import { required } from '../../../util/validators';

import { FormColumnLayout } from '../../../components/FormLayout';

function UserTokenFormFields() {
  const [applicationField, applicationMeta, applicationHelpers] = useField(
    'application'
  );

  const [scopeField, scopeMeta, scopeHelpers] = useField({
    name: 'scope',
    validate: required(t`Please enter a value.`),
  });

  return (
    <>
      <FormGroup
        fieldId="application-lookup"
        name="application"
        validated={
          !applicationMeta.touched || !applicationMeta.error
            ? 'default'
            : 'error'
        }
        helperTextInvalid={applicationMeta.error}
      >
        <ApplicationLookup
          value={applicationField.value}
          onChange={value => {
            applicationHelpers.setValue(value);
          }}
          label={
            <span>
              {t`Application`}
              <Popover
                content={t`Select the application that this token will belong to.`}
              />
            </span>
          }
          touched={applicationMeta.touched}
        />
      </FormGroup>
      <FormField
        id="token-description"
        name="description"
        type="text"
        label={t`Description`}
      />

      <FormGroup
        name="scope"
        fieldId="token-scope"
        helperTextInvalid={scopeMeta.error}
        isRequired
        validated={!scopeMeta.touched || !scopeMeta.error ? 'default' : 'error'}
        label={t`Scope`}
        labelIcon={
          <Popover content={t`Specify a scope for the token's access`} />
        }
      >
        <AnsibleSelect
          {...scopeField}
          id="token-scope"
          data={[
            { key: 'default', label: '', value: '' },
            { key: 'read', value: 'read', label: t`Read` },
            { key: 'write', value: 'write', label: t`Write` },
          ]}
          onChange={(event, value) => {
            scopeHelpers.setValue(value);
          }}
        />
      </FormGroup>
    </>
  );
}

function UserTokenForm({
  handleCancel,
  handleSubmit,
  submitError,

  token = {},
}) {
  return (
    <Formik
      initialValues={{
        description: token.description || '',
        application: token.application || null,
        scope: token.scope || '',
      }}
      onSubmit={handleSubmit}
    >
      {formik => (
        <Form autoComplete="off" onSubmit={formik.handleSubmit}>
          <FormColumnLayout>
            <UserTokenFormFields />
            {submitError && <FormSubmitError error={submitError} />}
            <FormActionGroup
              onCancel={handleCancel}
              onSubmit={() => {
                formik.handleSubmit();
              }}
            />
          </FormColumnLayout>
        </Form>
      )}
    </Formik>
  );
}
export default UserTokenForm;
