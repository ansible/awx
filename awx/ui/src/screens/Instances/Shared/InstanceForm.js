import React, { useCallback } from 'react';
import { t } from '@lingui/macro';
import { Formik, useField, useFormikContext } from 'formik';
import { Form, FormGroup, CardBody } from '@patternfly/react-core';
import { FormColumnLayout } from 'components/FormLayout';
import FormField, {
  FormSubmitError,
  CheckboxField,
} from 'components/FormField';
import FormActionGroup from 'components/FormActionGroup';
import AnsibleSelect from 'components/AnsibleSelect';
import { PeersLookup } from 'components/Lookup';
import { required } from 'util/validators';

const INSTANCE_TYPES = [
  { id: 'execution', name: t`Execution` },
  { id: 'hop', name: t`Hop` },
];

function InstanceFormFields({ isEdit }) {
  const [instanceTypeField, instanceTypeMeta, instanceTypeHelpers] = useField({
    name: 'node_type',
    validate: required(t`Set a value for this field`),
  });

  const { setFieldValue } = useFormikContext();

  const [peersField, peersMeta, peersHelpers] = useField('peers');

  const handlePeersUpdate = useCallback(
    (value) => {
      setFieldValue('peers', value);
    },
    [setFieldValue]
  );
  return (
    <>
      <FormField
        id="hostname"
        label={t`Host Name`}
        name="hostname"
        type="text"
        validate={required(null)}
        isRequired
        isDisabled={isEdit}
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
        fieldId="instance-type"
        label={t`Instance Type`}
        tooltip={t`Sets the role that this instance will play within mesh topology. Default is "execution."`}
        validated={
          !instanceTypeMeta.touched || !instanceTypeMeta.error
            ? 'default'
            : 'error'
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
          isDisabled={isEdit}
        />
      </FormGroup>
      <PeersLookup
        helperTextInvalid={peersMeta.error}
        isValid={!peersMeta.touched || !peersMeta.error}
        onBlur={() => peersHelpers.setTouched()}
        onChange={handlePeersUpdate}
        value={peersField.value}
        tooltip={t`Select the Peers Instances.`}
        fieldName="peers"
        formLabel={t`Peers`}
        multiple
        typePeers
        id="peers"
        isRequired
      />
      <FormGroup fieldId="instance-option-checkboxes" label={t`Options`}>
        <CheckboxField
          id="enabled"
          name="enabled"
          label={t`Enable Instance`}
          tooltip={t`Set the instance enabled or disabled. If disabled, jobs will not be assigned to this instance.`}
        />
        <CheckboxField
          id="managed-by-policy"
          name="managed_by_policy"
          label={t`Managed by Policy`}
          tooltip={t`Controls whether or not this instance is managed by policy. If enabled, the instance will be available for automatic assignment to and unassignment from instance groups based on policy rules.`}
        />
        <CheckboxField
          id="peers_from_control_nodes"
          name="peers_from_control_nodes"
          label={t`Connect to control nodes`}
          tooltip={t`Connect this instance to control nodes. If disabled, instance will be connected only to peers selected.`}
        />
      </FormGroup>
    </>
  );
}

function InstanceForm({
  instance = {},
  instance_peers = [],
  isEdit = false,
  submitError,
  handleCancel,
  handleSubmit,
}) {
  return (
    <CardBody>
      <Formik
        initialValues={{
          hostname: instance.hostname || '',
          description: instance.description || '',
          node_type: instance.node_type || 'execution',
          node_state: instance.node_state || 'installed',
          listener_port: instance.listener_port || 27199,
          enabled: instance.enabled || true,
          managed_by_policy: instance.managed_by_policy || true,
          peers_from_control_nodes: instance.peers_from_control_nodes
            ? true
            : !isEdit,
          peers: instance_peers,
        }}
        onSubmit={(values) => {
          handleSubmit({
            ...values,
            peers: values.peers.map((peer) => peer.hostname || peer),
          });
        }}
      >
        {(formik) => (
          <Form autoComplete="off" onSubmit={formik.handleSubmit}>
            <FormColumnLayout>
              <InstanceFormFields isEdit={isEdit} />
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
