import React from 'react';
import { func, shape } from 'prop-types';
import { Formik } from 'formik';

import { t } from '@lingui/macro';
import { Form } from '@patternfly/react-core';

import FormField, { FormSubmitError } from 'components/FormField';
import FormActionGroup from 'components/FormActionGroup';
import { required, minMaxValue } from 'util/validators';
import { FormColumnLayout } from 'components/FormLayout';

function InstanceGroupFormFields() {
  return (
    <>
      <FormField
        name="name"
        id="instance-group-name"
        label={t`Name`}
        type="text"
        validate={required(null)}
        isRequired
      />
      <FormField
        id="instance-group-policy-instance-minimum"
        label={t`Policy instance minimum`}
        name="policy_instance_minimum"
        type="number"
        min="0"
        validate={minMaxValue(0, 2147483647)}
        tooltip={t`Minimum number of instances that will be automatically
          assigned to this group when new instances come online.`}
      />
      <FormField
        id="instance-group-policy-instance-percentage"
        label={t`Policy instance percentage`}
        name="policy_instance_percentage"
        type="number"
        min="0"
        max="100"
        tooltip={t`Minimum percentage of all instances that will be automatically
          assigned to this group when new instances come online.`}
        validate={minMaxValue(0, 100)}
      />
    </>
  );
}

function InstanceGroupForm({
  instanceGroup = {},
  onSubmit,
  onCancel,
  submitError,
  ...rest
}) {
  const initialValues = {
    name: instanceGroup.name || '',
    policy_instance_minimum: instanceGroup.policy_instance_minimum || 0,
    policy_instance_percentage: instanceGroup.policy_instance_percentage || 0,
  };
  return (
    <Formik
      initialValues={initialValues}
      onSubmit={(values) => onSubmit(values)}
    >
      {(formik) => (
        <Form autoComplete="off" onSubmit={formik.handleSubmit}>
          <FormColumnLayout>
            <InstanceGroupFormFields {...rest} />
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

InstanceGroupForm.propTypes = {
  instanceGroup: shape({}),
  onCancel: func.isRequired,
  onSubmit: func.isRequired,
  submitError: shape({}),
};

InstanceGroupForm.defaultProps = {
  instanceGroup: {},
  submitError: null,
};

export default InstanceGroupForm;
