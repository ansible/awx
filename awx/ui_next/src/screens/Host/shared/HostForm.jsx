import React, { useState } from 'react';
import { func, shape } from 'prop-types';

import { useRouteMatch } from 'react-router-dom';
import { Formik, Field } from 'formik';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import { Form } from '@patternfly/react-core';

import FormRow from '@components/FormRow';
import FormField, { FormSubmitError } from '@components/FormField';
import FormActionGroup from '@components/FormActionGroup/FormActionGroup';
import { VariablesField } from '@components/CodeMirrorInput';
import { required } from '@util/validators';
import { InventoryLookup } from '@components/Lookup';

function HostForm({ handleSubmit, handleCancel, host, submitError, i18n }) {
  const [inventory, setInventory] = useState(
    host ? host.summary_fields.inventory : ''
  );

  const hostAddMatch = useRouteMatch('/hosts/add');

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
          <FormRow>
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
              <Field
                name="inventory"
                validate={required(
                  i18n._(t`Select a value for this field`),
                  i18n
                )}
              >
                {({ form }) => (
                  <InventoryLookup
                    value={inventory}
                    onBlur={() => form.setFieldTouched('inventory')}
                    tooltip={i18n._(
                      t`Select the inventory that this host will belong to.`
                    )}
                    isValid={!form.touched.inventory || !form.errors.inventory}
                    helperTextInvalid={form.errors.inventory}
                    onChange={value => {
                      form.setFieldValue('inventory', value.id);
                      setInventory(value);
                    }}
                    required
                    touched={form.touched.inventory}
                    error={form.errors.inventory}
                  />
                )}
              </Field>
            )}
          </FormRow>
          <FormRow>
            <VariablesField
              id="host-variables"
              name="variables"
              label={i18n._(t`Variables`)}
            />
          </FormRow>
          <FormSubmitError error={submitError} />
          <FormActionGroup
            onCancel={handleCancel}
            onSubmit={formik.handleSubmit}
          />
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
