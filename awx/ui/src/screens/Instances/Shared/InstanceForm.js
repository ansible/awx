import React from 'react';
import { t } from '@lingui/macro';
import { Formik } from 'formik';
import { Form, FormGroup, CardBody } from '@patternfly/react-core';
import { FormColumnLayout } from 'components/FormLayout';
import FormField, {
  FormSubmitError,
  CheckboxField,
} from 'components/FormField';
import FormActionGroup from 'components/FormActionGroup';
import { required } from 'util/validators';

function InstanceFormFields() {
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
      <FormField
        id="instance-type"
        label={t`Instance Type`}
        name="node_type"
        type="text"
        tooltip={t`Sets the role that this instance will play within mesh topology. Default is "execution."`}
        isDisabled
      />
      <FormGroup fieldId="instance-option-checkboxes" label={t`Options`}>
        <CheckboxField
          id="enabled"
          name="enabled"
          label={t`Enable Instance`}
          tooltip={t`Set the instance enabled or disabled. If disabled, jobs will not be assigned to this instance.`}
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
