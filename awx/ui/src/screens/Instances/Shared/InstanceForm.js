import React from 'react';
import { t } from '@lingui/macro';
import { Formik, useField } from 'formik';
import {
  Form,
  FormGroup,
  CardBody,
  Switch,
  Popover,
} from '@patternfly/react-core';
import { FormColumnLayout } from 'components/FormLayout';
import FormField, { FormSubmitError } from 'components/FormField';
import FormActionGroup from 'components/FormActionGroup';
import { required } from 'util/validators';
import AnsibleSelect from 'components/AnsibleSelect';

// This is hard coded because the API does not have the ability to send us a list that contains
// only the types of instances that can be added.  Control and Hybrid instances cannot be added.

const INSTANCE_TYPES = [
  { id: 'execution', name: t`Execution` },
  { id: 'hop', name: t`Hop` },
];

function InstanceFormFields() {
  const [instanceType, , instanceTypeHelpers] = useField('node_type');
  const [enabled, , enabledHelpers] = useField('enabled');
  return (
    <>
      <FormField
        id="name"
        label={t`Name`}
        name="hostname"
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
      <FormField
        id="instance-state"
        label={t`Instance State`}
        name="node_state"
        type="text"
        isDisabled
      />
      <FormField
        id="instance-port"
        label={t`Listener Port`}
        name="listener_port"
        type="number"
        isRequired
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
            value: type.id,
            label: type.name,
          }))}
          value={instanceType.value}
          onChange={(e, opt) => {
            instanceTypeHelpers.setValue(opt);
          }}
        />
      </FormGroup>
      <FormGroup
        label={t`Enable Instance`}
        aria-label={t`Enable Instance`}
        labelIcon={
          <Popover
            content={t`If enabled, the instance will be ready to accept work.`}
          />
        }
      >
        <Switch
          css="display: inline-flex;"
          id="enabled"
          label={t`Enabled`}
          labelOff={t`Disabled`}
          isChecked={enabled.value}
          onChange={() => {
            enabledHelpers.setValue(!enabled.value);
          }}
          ouiaId="enable-instance-switch"
        />
      </FormGroup>
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
          hostname: '',
          description: '',
          node_type: 'execution',
          node_state: 'Installed',
          listener_port: 27199,
          enabled: true,
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
