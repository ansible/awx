import React from 'react';
import { func, shape } from 'prop-types';
import { Formik } from 'formik';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Form } from '@patternfly/react-core';
import FormRow from '@components/FormRow';
import FormField from '@components/FormField';
import FormActionGroup from '@components/FormActionGroup/FormActionGroup';
import { VariablesField } from '@components/CodeMirrorInput';
import { required } from '@util/validators';

function InventoryHostForm({ handleSubmit, handleCancel, host, i18n }) {
  return (
    <Formik
      initialValues={{
        name: host.name,
        description: host.description,
        variables: host.variables,
      }}
      onSubmit={handleSubmit}
      render={formik => (
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
          </FormRow>
          <FormRow>
            <VariablesField
              id="host-variables"
              name="variables"
              label={i18n._(t`Variables`)}
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

InventoryHostForm.propTypes = {
  handleSubmit: func.isRequired,
  handleCancel: func.isRequired,
  host: shape({}),
};

InventoryHostForm.defaultProps = {
  host: {
    name: '',
    description: '',
    variables: '---\n',
  },
};

export default withI18n()(InventoryHostForm);
