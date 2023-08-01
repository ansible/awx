import React, { useCallback, useEffect } from 'react';
import { useHistory } from 'react-router-dom';
import { Formik } from 'formik';
import { Form } from '@patternfly/react-core';
import { CardBody } from 'components/Card';
import ContentError from 'components/ContentError';
import ContentLoading from 'components/ContentLoading';
import { FormSubmitError } from 'components/FormField';
import { FormColumnLayout } from 'components/FormLayout';
import { useSettings } from 'contexts/Settings';
import useModal from 'hooks/useModal';
import useRequest from 'hooks/useRequest';
import { SettingsAPI } from 'api';
import {
  BooleanField,
  RevertAllAlert,
  RevertFormActionGroup,
} from '../../shared';

function TroubleshootingEdit() {
  const history = useHistory();
  const { isModalOpen, toggleModal, closeModal } = useModal();
  const { PUT: options } = useSettings();

  const {
    isLoading,
    error,
    request: fetchJobs,
    result: debug,
  } = useRequest(
    useCallback(async () => {
      const { data } = await SettingsAPI.readCategory('debug');
      const { ...debugData } = data;
      const mergedData = {};
      Object.keys(debugData).forEach((key) => {
        if (!options[key]) {
          return;
        }
        mergedData[key] = options[key];
        mergedData[key].value = debugData[key];
      });

      return mergedData;
    }, [options]),
    null
  );

  useEffect(() => {
    fetchJobs();
  }, [fetchJobs]);

  const { error: submitError, request: submitForm } = useRequest(
    useCallback(
      async (values) => {
        await SettingsAPI.updateAll(values);
        history.push('/settings/troubleshooting/details');
      },
      [history]
    ),
    null
  );

  const { error: revertError, request: revertAll } = useRequest(
    useCallback(async () => {
      await SettingsAPI.revertCategory('debug');
    }, []),
    null
  );

  const handleSubmit = async (form) => {
    await submitForm({
      ...form,
    });
  };

  const handleRevertAll = async () => {
    await revertAll();

    closeModal();

    history.push('/settings/troubleshooting/details');
  };

  const handleCancel = () => {
    history.push('/settings/troubleshooting/details');
  };

  const initialValues = (fields) =>
    Object.keys(fields).reduce((acc, key) => {
      if (fields[key].type === 'list' || fields[key].type === 'nested object') {
        acc[key] = fields[key].value
          ? JSON.stringify(fields[key].value, null, 2)
          : null;
      } else {
        acc[key] = fields[key].value ?? '';
      }
      return acc;
    }, {});
  return (
    <CardBody>
      {isLoading && <ContentLoading />}
      {!isLoading && error && <ContentError error={error} />}
      {!isLoading && debug && (
        <Formik initialValues={initialValues(debug)} onSubmit={handleSubmit}>
          {(formik) => (
            <Form autoComplete="off" onSubmit={formik.handleSubmit}>
              <FormColumnLayout>
                <BooleanField
                  name="AWX_CLEANUP_PATHS"
                  config={debug.AWX_CLEANUP_PATHS}
                />
                <BooleanField
                  name="AWX_REQUEST_PROFILE"
                  config={debug.AWX_REQUEST_PROFILE}
                />
                <BooleanField
                  name="RECEPTOR_RELEASE_WORK"
                  config={debug.RECEPTOR_RELEASE_WORK}
                />
                {submitError && <FormSubmitError error={submitError} />}
                {revertError && <FormSubmitError error={revertError} />}
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
          )}
        </Formik>
      )}
    </CardBody>
  );
}

export default TroubleshootingEdit;
