import React, { useCallback, useEffect } from 'react';
import { useHistory } from 'react-router-dom';

import { t } from '@lingui/macro';
import { Formik } from 'formik';
import { Form } from '@patternfly/react-core';
import { CardBody } from 'components/Card';
import ContentError from 'components/ContentError';
import ContentLoading from 'components/ContentLoading';
import { FormSubmitError } from 'components/FormField';
import { FormColumnLayout, FormFullWidthLayout } from 'components/FormLayout';
import { useSettings } from 'contexts/Settings';
import useModal from 'hooks/useModal';
import useRequest from 'hooks/useRequest';
import { SettingsAPI } from 'api';
import { formatJson } from '../../shared/settingUtils';
import {
  BooleanField,
  ChoiceField,
  EncryptedField,
  InputField,
  ObjectField,
  RevertAllAlert,
  RevertFormActionGroup,
} from '../../shared';

function LoggingEdit() {
  const history = useHistory();
  const { isModalOpen, toggleModal, closeModal } = useModal();
  const { PUT: options } = useSettings();

  const {
    isLoading,
    error,
    request: fetchLogging,
    result: logging,
  } = useRequest(
    useCallback(async () => {
      const { data } = await SettingsAPI.readCategory('logging');
      const mergedData = {};
      Object.keys(data).forEach((key) => {
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
    fetchLogging();
  }, [fetchLogging]);

  const { error: submitError, request: submitForm } = useRequest(
    useCallback(
      async (values) => {
        await SettingsAPI.updateAll(values);
        history.push('/settings/logging/details');
      },
      [history]
    ),
    null
  );

  const handleSubmit = async (form) => {
    await submitForm({
      ...form,
      LOG_AGGREGATOR_LOGGERS: formatJson(form.LOG_AGGREGATOR_LOGGERS),
      LOG_AGGREGATOR_HOST: form.LOG_AGGREGATOR_HOST || null,
      LOG_AGGREGATOR_TYPE: form.LOG_AGGREGATOR_TYPE || null,
      API_400_ERROR_LOG_FORMAT: form.API_400_ERROR_LOG_FORMAT || null,
    });
  };

  const { error: revertError, request: revertAll } = useRequest(
    useCallback(async () => {
      await SettingsAPI.revertCategory('logging');
    }, []),
    null
  );

  const handleRevertAll = async () => {
    await revertAll();

    closeModal();

    history.push('/settings/logging/details');
  };

  const handleCancel = () => {
    history.push('/settings/logging/details');
  };

  const initialValues = (fields) =>
    Object.keys(fields).reduce((acc, key) => {
      if (fields[key].type === 'list') {
        acc[key] = JSON.stringify(fields[key].value, null, 2);
      } else {
        acc[key] = fields[key].value ?? '';
      }
      return acc;
    }, {});

  return (
    <CardBody>
      {isLoading && <ContentLoading />}
      {!isLoading && error && <ContentError error={error} />}
      {!isLoading && logging && (
        <Formik initialValues={initialValues(logging)} onSubmit={handleSubmit}>
          {(formik) => (
            <Form autoComplete="off" onSubmit={formik.handleSubmit}>
              <FormColumnLayout>
                <BooleanField
                  name="LOG_AGGREGATOR_ENABLED"
                  config={{
                    ...logging.LOG_AGGREGATOR_ENABLED,
                    help_text: (
                      <>
                        {logging.LOG_AGGREGATOR_ENABLED?.help_text}
                        {!formik.values.LOG_AGGREGATOR_ENABLED &&
                          (!formik.values.LOG_AGGREGATOR_HOST ||
                            !formik.values.LOG_AGGREGATOR_TYPE) && (
                            <>
                              <br />
                              <br />
                              {t`Cannot enable log aggregator without providing
                                  logging aggregator host and logging aggregator type.`}
                            </>
                          )}
                      </>
                    ),
                  }}
                  ariaLabel={t`Enable external logging`}
                  disabled={
                    !formik.values.LOG_AGGREGATOR_ENABLED &&
                    (!formik.values.LOG_AGGREGATOR_HOST ||
                      !formik.values.LOG_AGGREGATOR_TYPE)
                  }
                />
                <InputField
                  name="LOG_AGGREGATOR_HOST"
                  config={logging.LOG_AGGREGATOR_HOST}
                  isRequired={Boolean(formik.values.LOG_AGGREGATOR_ENABLED)}
                />
                <InputField
                  name="LOG_AGGREGATOR_PORT"
                  config={logging.LOG_AGGREGATOR_PORT}
                  type="number"
                />
                <ChoiceField
                  name="LOG_AGGREGATOR_TYPE"
                  config={logging.LOG_AGGREGATOR_TYPE}
                  isRequired={Boolean(formik.values.LOG_AGGREGATOR_ENABLED)}
                />
                <InputField
                  name="LOG_AGGREGATOR_USERNAME"
                  config={logging.LOG_AGGREGATOR_USERNAME}
                />
                <EncryptedField
                  name="LOG_AGGREGATOR_PASSWORD"
                  config={logging.LOG_AGGREGATOR_PASSWORD}
                />
                <BooleanField
                  name="LOG_AGGREGATOR_INDIVIDUAL_FACTS"
                  ariaLabel={t`Enable log system tracking facts individually`}
                  config={logging.LOG_AGGREGATOR_INDIVIDUAL_FACTS}
                />
                <ChoiceField
                  name="LOG_AGGREGATOR_PROTOCOL"
                  config={logging.LOG_AGGREGATOR_PROTOCOL}
                />
                <ChoiceField
                  name="LOG_AGGREGATOR_LEVEL"
                  config={logging.LOG_AGGREGATOR_LEVEL}
                />
                {['tcp', 'https'].includes(
                  formik.values.LOG_AGGREGATOR_PROTOCOL
                ) && (
                  <InputField
                    name="LOG_AGGREGATOR_TCP_TIMEOUT"
                    config={logging.LOG_AGGREGATOR_TCP_TIMEOUT}
                    type="number"
                    isRequired
                  />
                )}
                {formik.values.LOG_AGGREGATOR_PROTOCOL === 'https' && (
                  <BooleanField
                    name="LOG_AGGREGATOR_VERIFY_CERT"
                    ariaLabel={t`Enable HTTPS certificate verification`}
                    config={logging.LOG_AGGREGATOR_VERIFY_CERT}
                  />
                )}
                <ObjectField
                  name="LOG_AGGREGATOR_LOGGERS"
                  config={logging.LOG_AGGREGATOR_LOGGERS}
                />
                <FormFullWidthLayout>
                  <InputField
                    name="API_400_ERROR_LOG_FORMAT"
                    config={logging.API_400_ERROR_LOG_FORMAT}
                  />
                </FormFullWidthLayout>
                {submitError && <FormSubmitError error={submitError} />}
                {revertError && <FormSubmitError error={revertError} />}
                <RevertFormActionGroup
                  onCancel={handleCancel}
                  onSubmit={formik.handleSubmit}
                  onRevert={toggleModal}
                />
              </FormColumnLayout>
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

export default LoggingEdit;
