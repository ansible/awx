import React from 'react';

import { t } from '@lingui/macro';
import { Form, FormGroup, Modal } from '@patternfly/react-core';
import { InstancesAPI } from 'api';
import { Formik } from 'formik';
import { FormColumnLayout } from 'components/FormLayout';
import FormField, {
  CheckboxField,
} from 'components/FormField';
import FormActionGroup from '../FormActionGroup/FormActionGroup';

function AddEndpointModal({
  title = t`Add endpoint`,
  onClose,
  isAddEndpointModalOpen = false,
  instance,
  ouiaId,
}) {

  const handleClose = () => {
    onClose();
  };

  const handleEndpointAdd = async (values) => {
    try {
      values.id = instance.id;
      InstancesAPI.updateReceptorAddresses(instance.id, values);
      onClose();
    } catch (error) {
      // do nothing
    }
  };

  return (
    <Modal
      ouiaId={ouiaId}
      variant="large"
      title={title}
      aria-label={t`Add Endpoint modal`}
      isOpen={isAddEndpointModalOpen}
      onClose={handleClose}
      actions={[]}
    >
      <Formik
        initialValues={{
          listener_port: 1001
        }}
        onSubmit={handleEndpointAdd}
      >
        {(formik) => (
          <Form autoComplete="off" onSubmit={formik.handleSubmit}>
            <FormColumnLayout>
              <FormField
                id="address"
                label={t`Address`}
                name="address"
                type="text"
              />

              <FormField
                id="websocket_path"
                label={t`Websocket path`}
                name="websocket path"
                type="text"
              />

              <FormField
                id="listener_port"
                label={t`Listener Port`}
                name="listener_port"
                type="number"
                tooltip={t`Select the port that Receptor will listen on for incoming connections, e.g. 27199.`}
              />

              <FormGroup fieldId="endpoint" label={t`Options`}>
                <CheckboxField
                  id="peers_from_control_nodes"
                  name="peers_from_control_nodes"
                  label={t`Peers from control nodes`}
                  tooltip={t`If enabled, control nodes will peer to this instance automatically. If disabled, instance will be connected only to associated peers.`}
                />
              </FormGroup>

              <FormActionGroup
                onCancel={handleClose}
                onSubmit={formik.handleSubmit}
              />
            </FormColumnLayout>
          </Form>
        )}
      </Formik>
    </Modal>
  );
}

export default AddEndpointModal;