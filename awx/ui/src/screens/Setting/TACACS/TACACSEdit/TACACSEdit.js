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
  ChoiceField,
  EncryptedField,
  InputField,
} from '../../shared/SharedFields';
import { RevertAllAlert, RevertFormActionGroup } from '../../shared';

function TACACSEdit() {
  const history = useHistory();
  const { isModalOpen, toggleModal, closeModal } = useModal();
  const { PUT: options } = useSettings();

  const {
    isLoading,
    error,
    request: fetchTACACS,
    result: tacacs,
  } = useRequest(
    useCallback(async () => {
      const { data } = await SettingsAPI.readCategory('tacacsplus');
      const mergedData = {};
      Object.keys(data).forEach((key) => {
        mergedData[key] = options[key];
        mergedData[key].value = data[key];
      });
      return mergedData;
    }, [options]),
    null
  );

  useEffect(() => {
    fetchTACACS();
  }, [fetchTACACS]);

  const { error: submitError, request: submitForm } = useRequest(
    useCallback(
      async (values) => {
        await SettingsAPI.updateAll(values);
        history.push('/settings/tacacs/details');
      },
      [history]
    ),
    null
  );

  const { error: revertError, request: revertAll } = useRequest(
    useCallback(async () => {
      await SettingsAPI.revertCategory('tacacsplus');
    }, []),
    null
  );

  const handleSubmit = async (form) => {
    await submitForm(form);
  };

  const handleRevertAll = async () => {
    await revertAll();

    closeModal();

    history.push('/settings/tacacs/details');
  };

  const handleCancel = () => {
    history.push('/settings/tacacs/details');
  };

  const initialValues = (fields) =>
    Object.keys(fields).reduce((acc, key) => {
      acc[key] = fields[key].value ?? '';
      return acc;
    }, {});

  return (
    <CardBody>
      {isLoading && <ContentLoading />}
      {!isLoading && error && <ContentError error={error} />}
      {!isLoading && tacacs && (
        <Formik initialValues={initialValues(tacacs)} onSubmit={handleSubmit}>
          {(formik) => (
            <Form autoComplete="off" onSubmit={formik.handleSubmit}>
              <FormColumnLayout>
                <InputField
                  name="TACACSPLUS_HOST"
                  config={tacacs.TACACSPLUS_HOST}
                />
                <InputField
                  name="TACACSPLUS_PORT"
                  config={tacacs.TACACSPLUS_PORT}
                  type="number"
                />
                <EncryptedField
                  name="TACACSPLUS_SECRET"
                  config={tacacs.TACACSPLUS_SECRET}
                />
                <InputField
                  name="TACACSPLUS_SESSION_TIMEOUT"
                  config={tacacs.TACACSPLUS_SESSION_TIMEOUT}
                  type="number"
                />
                <ChoiceField
                  name="TACACSPLUS_AUTH_PROTOCOL"
                  config={tacacs.TACACSPLUS_AUTH_PROTOCOL}
                />
                <BooleanField
                  name="TACACSPLUS_REM_ADDR"
                  config={tacacs.TACACSPLUS_REM_ADDR}
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

export default TACACSEdit;
