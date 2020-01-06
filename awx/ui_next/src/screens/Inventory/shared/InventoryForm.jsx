import React from 'react';
import { Formik, Field } from 'formik';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { func, number, shape } from 'prop-types';

import { VariablesField } from '@components/CodeMirrorInput';
import { Form } from '@patternfly/react-core';
import FormField from '@components/FormField';
import FormActionGroup from '@components/FormActionGroup/FormActionGroup';
import FormRow from '@components/FormRow';
import { required } from '@util/validators';
import InstanceGroupsLookup from '@components/Lookup/InstanceGroupsLookup';
import OrganizationLookup from '@components/Lookup/OrganizationLookup';
import CredentialLookup from '@components/Lookup/CredentialLookup';

function InventoryForm({
  inventory = {},
  i18n,
  onCancel,
  onSubmit,
  instanceGroups,
  credentialTypeId,
}) {
  const initialValues = {
    name: inventory.name || '',
    description: inventory.description || '',
    variables: inventory.variables || '---',
    organization:
      (inventory.summary_fields && inventory.summary_fields.organization) ||
      null,
    instanceGroups: instanceGroups || [],
    insights_credential:
      (inventory.summary_fields &&
        inventory.summary_fields.insights_credential) ||
      null,
  };
  return (
    <Formik
      initialValues={initialValues}
      onSubmit={values => {
        onSubmit(values);
      }}
      render={formik => (
        <Form autoComplete="off" onSubmit={formik.handleSubmit}>
          <FormRow>
            <FormField
              id="inventory-name"
              label={i18n._(t`Name`)}
              name="name"
              type="text"
              validate={required(null, i18n)}
              isRequired
            />
            <FormField
              id="inventory-description"
              label={i18n._(t`Description`)}
              name="description"
              type="text"
            />
            <Field
              id="inventory-organization"
              label={i18n._(t`Organization`)}
              name="organization"
              validate={required(
                i18n._(t`Select a value for this field`),
                i18n
              )}
              render={({ form, field }) => (
                <OrganizationLookup
                  helperTextInvalid={form.errors.organization}
                  isValid={
                    !form.touched.organization || !form.errors.organization
                  }
                  onBlur={() => form.setFieldTouched('organization')}
                  onChange={value => {
                    form.setFieldValue('organization', value);
                  }}
                  value={field.value}
                  touched={form.touched.organization}
                  error={form.errors.organization}
                  required
                />
              )}
            />
            <Field
              id="inventory-insights_credential"
              label={i18n._(t`Insights Credential`)}
              name="insights_credential"
              render={({ field, form }) => (
                <CredentialLookup
                  label={i18n._(t`Insights Credential`)}
                  credentialTypeId={credentialTypeId}
                  onChange={value =>
                    form.setFieldValue('insights_credential', value)
                  }
                  value={field.value}
                />
              )}
            />
          </FormRow>
          <FormRow>
            <Field
              id="inventory-instanceGroups"
              label={i18n._(t`Instance Groups`)}
              name="instanceGroups"
              render={({ field, form }) => (
                <InstanceGroupsLookup
                  value={field.value}
                  onChange={value => {
                    form.setFieldValue('instanceGroups', value);
                  }}
                />
              )}
            />
          </FormRow>
          <FormRow>
            <VariablesField
              tooltip={i18n._(
                t`Enter inventory variables using either JSON or YAML syntax. Use the radio button to toggle between the two. Refer to the Ansible Tower documentation for example syntax`
              )}
              id="inventory-variables"
              name="variables"
              label={i18n._(t`Variables`)}
            />
          </FormRow>
          <FormRow>
            <FormActionGroup
              onCancel={onCancel}
              onSubmit={formik.handleSubmit}
            />
          </FormRow>
        </Form>
      )}
    />
  );
}

InventoryForm.proptype = {
  handleSubmit: func.isRequired,
  handleCancel: func.isRequired,
  instanceGroups: shape(),
  inventory: shape(),
  credentialTypeId: number.isRequired,
};

InventoryForm.defaultProps = {
  inventory: {},
  instanceGroups: [],
};

export default withI18n()(InventoryForm);
