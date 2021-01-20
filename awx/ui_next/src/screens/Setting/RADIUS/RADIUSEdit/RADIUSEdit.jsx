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
import { EncryptedField, InputField } from '../../shared/SharedFields';
import useModal from '../../../../util/useModal';
import useRequest from '../../../../util/useRequest';
import { SettingsAPI } from '../../../../api';

function RADIUSEdit() {
  const history = useHistory();
  const { isModalOpen, toggleModal, closeModal } = useModal();
  const { PUT: options } = useSettings();

  const { isLoading, error, request: fetchRadius, result: radius } = useRequest(
    useCallback(async () => {
      const { data } = await SettingsAPI.readCategory('radius');
      const mergedData = {};
      Object.keys(data).forEach(key => {
        mergedData[key] = options[key];
        mergedData[key].value = data[key];
      });
      return mergedData;
    }, [options]),
    null
  );

  useEffect(() => {
    fetchRadius();
  }, [fetchRadius]);

  const { error: submitError, request: submitForm } = useRequest(
    useCallback(
      async values => {
        await SettingsAPI.updateAll(values);
        history.push('/settings/radius/details');
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
      ...Object.entries(radius).map(([key, value]) => ({
        [key]: value.default,
      }))
    );
    await submitForm(defaultValues);
    closeModal();
  };

  const handleCancel = () => {
    history.push('/settings/radius/details');
  };

  const initialValues = fields =>
    Object.keys(fields).reduce((acc, key) => {
      acc[key] = fields[key].value ?? '';
      return acc;
    }, {});

  return (
    <CardBody>
      {isLoading && <ContentLoading />}
      {!isLoading && error && <ContentError error={error} />}
      {!isLoading && radius && (
        <Formik initialValues={initialValues(radius)} onSubmit={handleSubmit}>
          {formik => (
            <Form autoComplete="off" onSubmit={formik.handleSubmit}>
              <FormColumnLayout>
                <InputField
                  name="RADIUS_SERVER"
                  config={radius.RADIUS_SERVER}
                />
                <InputField name="RADIUS_PORT" config={radius.RADIUS_PORT} />
                <EncryptedField
                  name="RADIUS_SECRET"
                  config={radius.RADIUS_SECRET}
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

export default RADIUSEdit;
