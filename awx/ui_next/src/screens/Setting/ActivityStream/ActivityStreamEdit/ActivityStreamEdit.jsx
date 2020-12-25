import React, { useCallback, useEffect } from 'react';
import { useHistory } from 'react-router-dom';
import { Formik } from 'formik';
import { Form } from '@patternfly/react-core';
import { CardBody } from '../../../../components/Card';
import ContentError from '../../../../components/ContentError';
import ContentLoading from '../../../../components/ContentLoading';
import { FormSubmitError } from '../../../../components/FormField';
import { FormColumnLayout } from '../../../../components/FormLayout';
import { useSettings } from '../../../../contexts/Settings';
import {
  BooleanField,
  RevertAllAlert,
  RevertFormActionGroup,
} from '../../shared';
import useModal from '../../../../util/useModal';
import useRequest from '../../../../util/useRequest';
import { SettingsAPI } from '../../../../api';

function ActivityStreamEdit() {
  const history = useHistory();
  const { isModalOpen, toggleModal, closeModal } = useModal();
  const { PUT: options } = useSettings();

  const {
    isLoading,
    error,
    request,
    result: {
      ACTIVITY_STREAM_ENABLED,
      ACTIVITY_STREAM_ENABLED_FOR_INVENTORY_SYNC,
    },
  } = useRequest(
    useCallback(async () => {
      const { data } = await SettingsAPI.readCategory('system');
      return {
        ACTIVITY_STREAM_ENABLED: {
          ...options.ACTIVITY_STREAM_ENABLED,
          value: data.ACTIVITY_STREAM_ENABLED,
        },
        ACTIVITY_STREAM_ENABLED_FOR_INVENTORY_SYNC: {
          ...options.ACTIVITY_STREAM_ENABLED_FOR_INVENTORY_SYNC,
          value: data.ACTIVITY_STREAM_ENABLED_FOR_INVENTORY_SYNC,
        },
      };
    }, [options]),
    {}
  );

  useEffect(() => {
    request();
  }, [request]);

  const { error: submitError, request: submitForm } = useRequest(
    useCallback(
      async values => {
        await SettingsAPI.updateAll(values);
        history.push('/settings/activity_stream/details');
      },
      [history]
    ),
    null
  );

  const handleSubmit = async form => {
    await submitForm(form);
  };

  const handleCancel = () => {
    history.push('/settings/activity_stream/details');
  };

  const handleRevertAll = async () => {
    const defaultValues = {
      ACTIVITY_STREAM_ENABLED: ACTIVITY_STREAM_ENABLED.default,
      ACTIVITY_STREAM_ENABLED_FOR_INVENTORY_SYNC:
        ACTIVITY_STREAM_ENABLED_FOR_INVENTORY_SYNC.default,
    };
    await submitForm(defaultValues);
    closeModal();
  };

  return (
    <CardBody>
      {isLoading && <ContentLoading />}
      {!isLoading && error && <ContentError error={error} />}
      {!isLoading && ACTIVITY_STREAM_ENABLED && (
        <Formik
          initialValues={{
            ACTIVITY_STREAM_ENABLED: ACTIVITY_STREAM_ENABLED.value,
            ACTIVITY_STREAM_ENABLED_FOR_INVENTORY_SYNC:
              ACTIVITY_STREAM_ENABLED_FOR_INVENTORY_SYNC.value,
          }}
          onSubmit={handleSubmit}
        >
          {formik => {
            return (
              <Form autoComplete="off" onSubmit={formik.handleSubmit}>
                <FormColumnLayout>
                  <BooleanField
                    name="ACTIVITY_STREAM_ENABLED"
                    config={ACTIVITY_STREAM_ENABLED}
                  />
                  <BooleanField
                    name="ACTIVITY_STREAM_ENABLED_FOR_INVENTORY_SYNC"
                    config={ACTIVITY_STREAM_ENABLED_FOR_INVENTORY_SYNC}
                  />
                  {submitError && <FormSubmitError error={submitError} />}
                </FormColumnLayout>
                <RevertFormActionGroup
                  onCancel={handleCancel}
                  onSubmit={formik.handleSubmit}
                  onRevert={toggleModal}
                />
                {isModalOpen && (
                  <RevertAllAlert
                    onClose={closeModal}
                    onRevertAll={handleRevertAll}
                  />
                )}
              </Form>
            );
          }}
        </Formik>
      )}
    </CardBody>
  );
}

export default ActivityStreamEdit;
