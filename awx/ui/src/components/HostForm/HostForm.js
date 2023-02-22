import React, { useCallback } from 'react';
import { bool, func, shape } from 'prop-types';
import { Formik, useField, useFormikContext } from 'formik';
import { t } from '@lingui/macro';
import { Form, FormGroup, Tooltip } from '@patternfly/react-core';
import { required } from 'util/validators';
import FormField, { FormSubmitError } from '../FormField';
import FormActionGroup from '../FormActionGroup/FormActionGroup';
import { VariablesField } from '../CodeEditor';
import { InventoryLookup } from '../Lookup';
import { FormColumnLayout, FormFullWidthLayout } from '../FormLayout';
import Popover from '../Popover';

const InventoryLookupField = ({ isDisabled }) => {
  const { setFieldValue, setFieldTouched } = useFormikContext();
  const [inventoryField, inventoryMeta, inventoryHelpers] =
    useField('inventory');

  const handleInventoryUpdate = useCallback(
    (value) => {
      setFieldValue('inventory', value);
      setFieldTouched('inventory', true, false);
    },
    [setFieldValue, setFieldTouched]
  );

  const renderInventoryLookup = (
    <InventoryLookup
      fieldId="inventory-lookup"
      value={inventoryField.value}
      onBlur={() => inventoryHelpers.setTouched()}
      tooltip={t`Select the inventory that this host will belong to.`}
      isValid={!inventoryMeta.touched || !inventoryMeta.error}
      helperTextInvalid={inventoryMeta.error}
      onChange={handleInventoryUpdate}
      required
      touched={inventoryMeta.touched}
      error={inventoryMeta.error}
      validate={required(t`Select a value for this field`)}
      isDisabled={isDisabled}
      hideAdvancedInventories
      autoPopulate={!inventoryField.value?.id}
    />
  );

  return (
    <FormGroup
      label={t`Inventory`}
      labelIcon={
        <Popover
          content={t`Select the inventory that this host will belong to.`}
        />
      }
      isRequired
      fieldId="inventory-lookup"
      validated={
        !inventoryMeta.touched || !inventoryMeta.error ? 'default' : 'error'
      }
      helperTextInvalid={inventoryMeta.error}
    >
      {isDisabled ? (
        <Tooltip content={t`Unable to change inventory on a host`}>
          {renderInventoryLookup}
        </Tooltip>
      ) : (
        renderInventoryLookup
      )}
    </FormGroup>
  );
};

const HostForm = ({
  handleCancel,
  handleSubmit,
  host,
  isInventoryVisible,
  submitError,
  disableInventoryLookup,
}) => (
  <Formik
    initialValues={{
      name: host.name,
      description: host.description,
      inventory: host.summary_fields?.inventory || null,
      variables: host.variables,
    }}
    onSubmit={handleSubmit}
  >
    {(formik) => (
      <Form autoComplete="off" onSubmit={formik.handleSubmit}>
        <FormColumnLayout>
          <FormField
            id="host-name"
            name="name"
            type="text"
            label={t`Name`}
            validate={required(null)}
            isRequired
          />
          <FormField
            id="host-description"
            name="description"
            type="text"
            label={t`Description`}
          />
          {isInventoryVisible && (
            <InventoryLookupField isDisabled={disableInventoryLookup} />
          )}
          <FormFullWidthLayout>
            <VariablesField
              id="host-variables"
              name="variables"
              label={t`Variables`}
            />
          </FormFullWidthLayout>
          {submitError && <FormSubmitError error={submitError} />}
          <FormActionGroup
            onCancel={handleCancel}
            onSubmit={formik.handleSubmit}
          />
        </FormColumnLayout>
      </Form>
    )}
  </Formik>
);

HostForm.propTypes = {
  handleCancel: func.isRequired,
  handleSubmit: func.isRequired,
  host: shape({}),
  isInventoryVisible: bool,
  submitError: shape({}),
  disableInventoryLookup: bool,
};

HostForm.defaultProps = {
  host: {
    name: '',
    description: '',
    inventory: undefined,
    variables: '---\n',
    summary_fields: {
      inventory: null,
    },
  },
  isInventoryVisible: true,
  submitError: null,
  disableInventoryLookup: false,
};

export { HostForm as _HostForm };
export default HostForm;
