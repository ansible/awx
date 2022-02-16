import React from 'react';
import { func, shape } from 'prop-types';
import { Formik, useField } from 'formik';

import { t } from '@lingui/macro';
import { Form } from '@patternfly/react-core';

import FormField, { FormSubmitError } from 'components/FormField';
import FormActionGroup from 'components/FormActionGroup';
import {
  combine,
  required,
  protectedResourceName,
  minMaxValue,
} from 'util/validators';
import { FormColumnLayout } from 'components/FormLayout';

function InstanceGroupFormFields({ defaultControlPlane, defaultExecution }) {
  const [, { initialValue }] = useField('name');
  const isProtected =
    initialValue === `${defaultControlPlane}` ||
    initialValue === `${defaultExecution}`;

  const validators = combine([
    required(null),
    protectedResourceName(
      t`This is a protected name for Instance Groups. Please use a different name.`,
      [defaultControlPlane, defaultExecution]
    ),
  ]);

  return (
    <>
      <FormField
        name="name"
        helperText={
          isProtected
            ? t`This is a protected Instance Group. The name cannot be changed.`
            : ''
        }
        id="instance-group-name"
        label={t`Name`}
        type="text"
        validate={validators}
        isRequired
        isDisabled={isProtected}
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
