import React from 'react';
import { t } from '@lingui/macro';
import { Formik, useField } from 'formik';
import { Form, FormGroup, CardBody } from '@patternfly/react-core';
import { FormColumnLayout } from 'components/FormLayout';
import FormField, {
  FormSubmitError,
  CheckboxField,
} from 'components/FormField';
import FormActionGroup from 'components/FormActionGroup';
import AnsibleSelect from 'components/AnsibleSelect';
import { required } from 'util/validators';

const INSTANCE_TYPES = [
  { id: 'execution', name: t`Execution` },
  { id: 'hop', name: t`Hop` },
];

function InstanceFormFields() {
  const [instanceTypeField, instanceTypeMeta, instanceTypeHelpers] = useField({
    name: 'node_type',
    validate: required(t`Set a value for this field`),
  });

  return (
    <>
      <FormField
        id="hostname"
        label={t`Host Name`}
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
        tooltip={t`Sets the current life cycle stage of this instance. Default is "installed."`}
        isDisabled
      />
      <FormField
        id="instance-port"
        label={t`Listener Port`}
        name="listener_port"
        type="number"
        tooltip={t`Select the port that Receptor will listen on for incoming connections. Default is 27199.`}
        isRequired
      />
      <FormGroup
        fieldId="node_type"
        label={t`Instance Type`}
        tooltip={t`Sets the role that this instance will play within mesh topology. Default is "execution."`}
        validated={
          !instanceTypeMeta.touched || !instanceTypeMeta.error ? 'default' : 'error'
        }
        helperTextInvalid={instanceTypeMeta.error}
        isRequired
      >
        <AnsibleSelect
          {...instanceTypeField}
          id="node_type"
          data={INSTANCE_TYPES.map((type) => ({
            key: type.id,
            value: type.id,
            label: type.name,
          }))}
          onChange={(event, value) => {
            instanceTypeHelpers.setValue(value);
          }}
        />
      </FormGroup>
      <FormGroup fieldId="instance-option-checkboxes" label={t`Options`}>
        <CheckboxField
          id="enabled"
          name="enabled"
          label={t`Enable Instance`}
          tooltip={t`Set the instance enabled or disabled. If disabled, jobs will not be assigned to this instance.`}
        />
      </FormGroup>
      <FormGroup fieldId="peer-to-control-nodes-option-checkboxes" label={t`Options`}>
        <CheckboxField
          id="peer_to_control_nodes"
          name="peer_to_control_nodes"
          label={t`Connect to control nodes`}
          tooltip={t`Connect this instance to control nodes. If disabled, instance will be connected only to peers selected.`}
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
          node_state: 'installed',
          listener_port: 27199,
          enabled: true,
          peer_to_control_nodes: true,
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
