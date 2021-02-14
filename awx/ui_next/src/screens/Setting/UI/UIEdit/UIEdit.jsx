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
import { RevertAllAlert, RevertFormActionGroup } from '../../shared';
import {
  ChoiceField,
  FileUploadField,
  TextAreaField,
} from '../../shared/SharedFields';
import useModal from '../../../../util/useModal';
import useRequest from '../../../../util/useRequest';
import { SettingsAPI } from '../../../../api';

function UIEdit() {
  const history = useHistory();
  const { isModalOpen, toggleModal, closeModal } = useModal();
  const { PUT: options } = useSettings();

  const { isLoading, error, request: fetchUI, result: uiData } = useRequest(
    useCallback(async () => {
      const { data } = await SettingsAPI.readCategory('ui');
      const mergedData = {};
      Object.keys(data).forEach(key => {
        if (!options[key]) {
          return;
        }
        mergedData[key] = options[key];
        mergedData[key].value = data[key];
      });
      return mergedData;
    }, [options]),
    null
  );

  useEffect(() => {
    fetchUI();
  }, [fetchUI]);

  const { error: submitError, request: submitForm } = useRequest(
    useCallback(
      async values => {
        await SettingsAPI.updateAll(values);
        history.push('/settings/ui/details');
      },
      [history]
    ),
    null
  );

  const handleSubmit = async form => {
    await submitForm(form);
  };

  const handleRevertAll = async () => {
    const defaultValues = Object.assign(
      ...Object.entries(uiData).map(([key, value]) => ({
        [key]: value.default,
      }))
    );
    await submitForm(defaultValues);
    closeModal();
  };

  const handleCancel = () => {
    history.push('/settings/ui/details');
  };

  return (
    <CardBody>
      {isLoading && <ContentLoading />}
      {!isLoading && error && <ContentError error={error} />}
      {!isLoading && uiData && (
        <Formik
          initialValues={{
            PENDO_TRACKING_STATE: uiData?.PENDO_TRACKING_STATE?.value ?? 'off',
            CUSTOM_LOGIN_INFO: uiData?.CUSTOM_LOGIN_INFO?.value ?? '',
            CUSTOM_LOGO: uiData?.CUSTOM_LOGO?.value ?? '',
          }}
          onSubmit={handleSubmit}
        >
          {formik => (
            <Form autoComplete="off" onSubmit={formik.handleSubmit}>
              <FormColumnLayout>
                {uiData?.PENDO_TRACKING_STATE?.value !== 'off' && (
                  <ChoiceField
                    name="PENDO_TRACKING_STATE"
                    config={uiData.PENDO_TRACKING_STATE}
                    isRequired
                  />
                )}
                <TextAreaField
                  name="CUSTOM_LOGIN_INFO"
                  config={uiData.CUSTOM_LOGIN_INFO}
                />
                <FileUploadField
                  name="CUSTOM_LOGO"
                  config={uiData.CUSTOM_LOGO}
                  type="dataURL"
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
          )}
        </Formik>
      )}
    </CardBody>
  );
}

export default UIEdit;
