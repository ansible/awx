import React from 'react';
import { t } from '@lingui/macro';
import { Formik, useField } from 'formik';
import { Form, FormGroup, CardBody } from '@patternfly/react-core';
import { FormColumnLayout } from 'components/FormLayout';
import FormField, { FormSubmitError } from 'components/FormField';
import FormActionGroup from 'components/FormActionGroup';
import { required } from 'util/validators';
import AnsibleSelect from 'components/AnsibleSelect';
import {
  ExecutionEnvironmentLookup,
  InstanceGroupsLookup,
} from 'components/Lookup';

// This is hard coded because the API does not have the ability to send us a list that contains
// only the types of instances that can be added.  Control and Hybrid instances cannot be added.

const INSTANCE_TYPES = [
  { id: 2, name: t`Execution`, value: 'execution' },
  { id: 3, name: t`Hop`, value: 'hop' },
];

function InstanceFormFields() {
  const [instanceType, , instanceTypeHelpers] = useField('type');
  const [instanceGroupsField, , instanceGroupsHelpers] =
    useField('instanceGroups');
  const [
    executionEnvironmentField,
    executionEnvironmentMeta,
    executionEnvironmentHelpers,
  ] = useField('executionEnvironment');
  return (
    <>
      <FormField
        id="instance-name"
        label={t`Name`}
        name="name"
        type="text"
        validate={required(null)}
        isRequired
      />
      <FormField
        id="instance-description"
        label={t`Description`}
        name="description"
        type="text"
      />
      <FormGroup
        fieldId="instanceType"
        label={t`Instance Type`}
        name="type"
        isRequired
        validated={required(null)}
      >
        <AnsibleSelect
          {...instanceType}
          id="instanceType-select"
          data={INSTANCE_TYPES.map((type) => ({
            key: type.id,
            value: type.value,
            label: type.name,
            isDisabled: false,
          }))}
          value={instanceType.value}
          onChange={(e, opt) => {
            instanceTypeHelpers.setValue(opt);
          }}
        />
      </FormGroup>
      <InstanceGroupsLookup
        value={instanceGroupsField.value}
        onChange={(value) => {
          instanceGroupsHelpers.setValue(value);
        }}
        fieldName="instanceGroups"
      />
      <ExecutionEnvironmentLookup
        helperTextInvalid={executionEnvironmentMeta.error}
        isValid={
          !executionEnvironmentMeta.touched || !executionEnvironmentMeta.error
        }
        fieldName={executionEnvironmentField.name}
        onBlur={() => executionEnvironmentHelpers.setTouched()}
        value={executionEnvironmentField.value}
        onChange={(value) => {
          executionEnvironmentHelpers.setValue(value);
        }}
      />
    </>
  );
}

function InstanceForm({
  instance = {},
  submitError,
  handleCancel,
  handleSubmit,
}) {
  return (
    <CardBody>
      <Formik
        initialValues={{
          name: instance.name || '',
          description: instance.description || '',
          type: instance.type || 'execution',
          instanceGroups: instance.instance_groups || [],
          executionEnvironment: instance.execution_environment || null,
        }}
        onSubmit={(values) => {
          handleSubmit(values);
        }}
      >
        {(formik) => (
          <Form autoComplete="off" onSubmit={formik.handleSubmit}>
            <FormColumnLayout>
              <InstanceFormFields instance={instance} />
              <FormSubmitError error={submitError} />
              <FormActionGroup
                onCancel={handleCancel}
                onSubmit={formik.handleSubmit}
              />
            </FormColumnLayout>
          </Form>
        )}
      </Formik>
    </CardBody>
  );
}

export default InstanceForm;
