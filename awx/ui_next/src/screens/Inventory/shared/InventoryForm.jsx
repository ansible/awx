import React, { useState } from 'react';
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
  handleCancel,
  handleSubmit,
  instanceGroups,
  credentialTypeId,
}) {
  const [organization, setOrganization] = useState(
    inventory.summary_fields ? inventory.summary_fields.organization : null
  );
  const [insights_credential, setInsights_Credential] = useState(
    inventory.summary_fields
      ? inventory.summary_fields.insights_credential
      : null
  );

  const initialValues = {
    name: inventory.name || '',
    description: inventory.description || '',
    variables: inventory.variables || '---',
    organization: organization ? organization.id : null,
    instance_groups: instanceGroups || [],
    insights_credential: insights_credential ? insights_credential.id : '',
  };
  return (
    <Formik
      initialValues={initialValues}
      onSubmit={values => {
        handleSubmit(values);
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
          </FormRow>
          <FormRow>
            <Field
              id="inventory-insights_credential"
              label={i18n._(t`Insights Credential`)}
              name="insights_credential"
              render={({ form }) => (
                <CredentialLookup
                  label={i18n._(t`Insights Credential`)}
                  credentialTypeId={credentialTypeId}
                  onChange={value => {
                    form.setFieldValue('insights_credential', value.id);
                    setInsights_Credential(value);
                  }}
                  value={insights_credential}
                />
              )}
            />
          </FormRow>
          <FormRow>
            <Field
              id="inventory-instanceGroups"
              label={i18n._(t`Instance Groups`)}
              name="instance_groups"
              render={({ field, form }) => (
                <InstanceGroupsLookup
                  value={field.value}
                  onChange={value => {
                    form.setFieldValue('instance_groups', value);
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
              onCancel={handleCancel}
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
  credentialTypeId: number,
};

InventoryForm.defaultProps = {
  credentialTypeId: 14,
  inventory: {},
  instanceGroups: [],
};

export default withI18n()(InventoryForm);
