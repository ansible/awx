import React, { useCallback } from 'react';
import { Formik, useField, useFormikContext } from 'formik';
import { t } from '@lingui/macro';
import { func, shape } from 'prop-types';
import { Form } from '@patternfly/react-core';
import { VariablesField } from 'components/CodeEditor';
import FormField, { FormSubmitError } from 'components/FormField';
import FormActionGroup from 'components/FormActionGroup';
import { required } from 'util/validators';
import InstanceGroupsLookup from 'components/Lookup/InstanceGroupsLookup';
import OrganizationLookup from 'components/Lookup/OrganizationLookup';
import { FormColumnLayout, FormFullWidthLayout } from 'components/FormLayout';

function InventoryFormFields({ inventory }) {
  const { setFieldValue, setFieldTouched } = useFormikContext();
  const [organizationField, organizationMeta, organizationHelpers] =
    useField('organization');
  const [instanceGroupsField, , instanceGroupsHelpers] =
    useField('instanceGroups');
  const handleOrganizationUpdate = useCallback(
    (value) => {
      setFieldValue('organization', value);
      setFieldTouched('organization', true, false);
    },
    [setFieldValue, setFieldTouched]
  );

  return (
    <>
      <FormField
        id="inventory-name"
        label={t`Name`}
        name="name"
        type="text"
        validate={required(null)}
        isRequired
      />
      <FormField
        id="inventory-description"
        label={t`Description`}
        name="description"
        type="text"
      />
      <OrganizationLookup
        helperTextInvalid={organizationMeta.error}
        isValid={!organizationMeta.touched || !organizationMeta.error}
        onBlur={() => organizationHelpers.setTouched()}
        onChange={handleOrganizationUpdate}
        value={organizationField.value}
        touched={organizationMeta.touched}
        error={organizationMeta.error}
        required
        autoPopulate={!inventory?.id}
        validate={required(t`Select a value for this field`)}
      />
      <InstanceGroupsLookup
        value={instanceGroupsField.value}
        onChange={(value) => {
          instanceGroupsHelpers.setValue(value);
        }}
        fieldName="instanceGroups"
      />
      <FormFullWidthLayout>
        <VariablesField
          tooltip={t`Enter inventory variables using either JSON or YAML syntax. Use the radio button to toggle between the two. Refer to the Ansible Tower documentation for example syntax`}
          id="inventory-variables"
          name="variables"
          label={t`Variables`}
        />
      </FormFullWidthLayout>
    </>
  );
}

function InventoryForm({
  inventory = {},
  onSubmit,
  onCancel,
  submitError,
  instanceGroups,
  ...rest
}) {
  const initialValues = {
    name: inventory.name || '',
    description: inventory.description || '',
    variables: inventory.variables || '---',
    organization:
      (inventory.summary_fields && inventory.summary_fields.organization) ||
      null,
    instanceGroups: instanceGroups || [],
  };

  return (
    <Formik
      initialValues={initialValues}
      onSubmit={(values) => {
        onSubmit(values);
      }}
    >
      {(formik) => (
        <Form autoComplete="off" onSubmit={formik.handleSubmit}>
          <FormColumnLayout>
            <InventoryFormFields {...rest} inventory={inventory} />
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

InventoryForm.propType = {
  handleSubmit: func.isRequired,
  handleCancel: func.isRequired,
  instanceGroups: shape(),
  inventory: shape(),
  submitError: shape(),
};

InventoryForm.defaultProps = {
  inventory: {},
  instanceGroups: [],
  submitError: null,
};

export default InventoryForm;
