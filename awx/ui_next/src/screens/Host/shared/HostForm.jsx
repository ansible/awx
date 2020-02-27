import React, { useState } from 'react';
import { func, shape } from 'prop-types';

import { useRouteMatch } from 'react-router-dom';
import { Formik, useField } from 'formik';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import { Form, FormGroup } from '@patternfly/react-core';

import FormField, {
  FormSubmitError,
  FieldTooltip,
} from '@components/FormField';
import FormActionGroup from '@components/FormActionGroup/FormActionGroup';
import { VariablesField } from '@components/CodeMirrorInput';
import { required } from '@util/validators';
import { InventoryLookup } from '@components/Lookup';
import { FormColumnLayout, FormFullWidthLayout } from '@components/FormLayout';

function HostFormFields({ host, i18n }) {
  const [inventory, setInventory] = useState(
    host ? host.summary_fields.inventory : ''
  );

  const hostAddMatch = useRouteMatch('/hosts/add');
  const inventoryFieldArr = useField({
    name: 'inventory',
    validate: required(i18n._(t`Select a value for this field`), i18n),
  });
  const inventoryMeta = inventoryFieldArr[1];
  const inventoryHelpers = inventoryFieldArr[2];

  return (
    <>
      <FormField
        id="host-name"
        name="name"
        type="text"
        label={i18n._(t`Name`)}
        validate={required(null, i18n)}
        isRequired
      />
      <FormField
        id="host-description"
        name="description"
        type="text"
        label={i18n._(t`Description`)}
      />
      {hostAddMatch && (
        <FormGroup
          label={i18n._(t`Inventory`)}
          isRequired
          fieldId="inventory-lookup"
          isValid={!inventoryMeta.touched || !inventoryMeta.error}
          helperTextInvalid={inventoryMeta.error}
        >
          <FieldTooltip
            content={i18n._(
              t`Select the inventory that this host will belong to.`
            )}
          />
          <InventoryLookup
            value={inventory}
            onBlur={() => inventoryHelpers.setTouched()}
            tooltip={i18n._(
              t`Select the inventory that this host will belong to.`
            )}
            isValid={!inventoryMeta.touched || !inventoryMeta.error}
            helperTextInvalid={inventoryMeta.error}
            onChange={value => {
              inventoryHelpers.setValue(value.id);
              setInventory(value);
            }}
            required
            touched={inventoryMeta.touched}
            error={inventoryMeta.error}
          />
        </FormGroup>
      )}
      <FormFullWidthLayout>
        <VariablesField
          id="host-variables"
          name="variables"
          label={i18n._(t`Variables`)}
        />
      </FormFullWidthLayout>
    </>
  );
}

function HostForm({ handleSubmit, host, submitError, handleCancel, ...rest }) {
  return (
    <Formik
      initialValues={{
        name: host.name,
        description: host.description,
        inventory: host.inventory || '',
        variables: host.variables,
      }}
      onSubmit={handleSubmit}
    >
      {formik => (
        <Form autoComplete="off" onSubmit={formik.handleSubmit}>
          <FormColumnLayout>
            <HostFormFields host={host} {...rest} />
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

HostForm.propTypes = {
  handleSubmit: func.isRequired,
  handleCancel: func.isRequired,
  host: shape({}),
  submitError: shape({}),
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
  submitError: null,
};

export { HostForm as _HostForm };
export default withI18n()(HostForm);
