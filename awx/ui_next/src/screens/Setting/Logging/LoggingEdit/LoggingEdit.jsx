import React, { useCallback, useEffect } from 'react';
import { useHistory } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Formik } from 'formik';
import { Button, Form, Tooltip } from '@patternfly/react-core';
import { CardBody } from '../../../../components/Card';
import ContentError from '../../../../components/ContentError';
import ContentLoading from '../../../../components/ContentLoading';
import { FormSubmitError } from '../../../../components/FormField';
import { FormColumnLayout } from '../../../../components/FormLayout';
import { useSettings } from '../../../../contexts/Settings';
import {
  BooleanField,
  ChoiceField,
  EncryptedField,
  InputField,
  ObjectField,
  RevertAllAlert,
  RevertFormActionGroup,
  LoggingTestAlert,
} from '../../shared';
import useModal from '../../../../util/useModal';
import useRequest, { useDismissableError } from '../../../../util/useRequest';
import { formatJson } from '../../shared/settingUtils';
import { SettingsAPI } from '../../../../api';

function LoggingEdit({ i18n }) {
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
    fetchLogging();
  }, [fetchLogging]);

  const { error: submitError, request: submitForm } = useRequest(
    useCallback(
      async values => {
        await SettingsAPI.updateAll(values);
        history.push('/settings/logging/details');
      },
      [history]
    ),
    null
  );

  const handleSubmit = async form => {
    await submitForm({
      ...form,
      LOG_AGGREGATOR_LOGGERS: formatJson(form.LOG_AGGREGATOR_LOGGERS),
      LOG_AGGREGATOR_HOST: form.LOG_AGGREGATOR_HOST || null,
      LOG_AGGREGATOR_TYPE: form.LOG_AGGREGATOR_TYPE || null,
    });
  };

  const handleRevertAll = async () => {
    const defaultValues = {};
    Object.entries(logging).forEach(([key, value]) => {
      defaultValues[key] = value.default;
    });

    await submitForm(defaultValues);
    closeModal();
  };

  const {
    error: testLoggingError,
    request: testLogging,
    result: testSuccess,
    setValue: setTestLogging,
  } = useRequest(
    useCallback(async () => {
      const result = await SettingsAPI.createTest('logging', {});
      return result;
    }, []),
    null
  );

  const {
    error: testError,
    dismissError: dismissTestError,
  } = useDismissableError(testLoggingError);

  const handleTest = async () => {
    await testLogging();
  };

  const handleCloseAlert = () => {
    setTestLogging(null);
    dismissTestError();
  };

  const handleCancel = () => {
    history.push('/settings/logging/details');
  };

  const initialValues = fields =>
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
          {formik => {
            return (
              <Form autoComplete="off" onSubmit={formik.handleSubmit}>
                <FormColumnLayout>
                  <BooleanField
                    name="LOG_AGGREGATOR_ENABLED"
                    config={{
                      ...logging.LOG_AGGREGATOR_ENABLED,
                      help_text: (
                        <>
                          {logging.LOG_AGGREGATOR_ENABLED.help_text}
                          {!formik.values.LOG_AGGREGATOR_ENABLED &&
                            (!formik.values.LOG_AGGREGATOR_HOST ||
                              !formik.values.LOG_AGGREGATOR_TYPE) && (
                              <>
                                <br />
                                <br />
                                {i18n._(
                                  t`Cannot enable log aggregator without providing
                                  logging aggregator host and logging aggregator type.`
                                )}
                              </>
                            )}
                        </>
                      ),
                    }}
                    ariaLabel={i18n._(t`Enable external logging`)}
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
                    ariaLabel={i18n._(
                      t`Enable log system tracking facts individually`
                    )}
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
                      ariaLabel={i18n._(
                        t`Enable HTTPS certificate verification`
                      )}
                      config={logging.LOG_AGGREGATOR_VERIFY_CERT}
                    />
                  )}
                  <ObjectField
                    name="LOG_AGGREGATOR_LOGGERS"
                    config={logging.LOG_AGGREGATOR_LOGGERS}
                  />
                  {submitError && <FormSubmitError error={submitError} />}
                  <RevertFormActionGroup
                    onCancel={handleCancel}
                    onSubmit={formik.handleSubmit}
                    onRevert={toggleModal}
                  >
                    <Tooltip
                      content={
                        formik.dirty || !formik.values.LOG_AGGREGATOR_ENABLED
                          ? i18n._(
                              t`Save and enable log aggregation before testing the log aggregator.`
                            )
                          : i18n._(
                              t`Send a test log message to the configured log aggregator.`
                            )
                      }
                    >
                      <div>
                        <Button
                          aria-label={i18n._(t`Test logging`)}
                          ouiaId="test-logging-button"
                          variant="secondary"
                          type="button"
                          onClick={handleTest}
                          isDisabled={
                            formik.dirty ||
                            !formik.values.LOG_AGGREGATOR_ENABLED ||
                            testSuccess ||
                            testError
                          }
                        >
                          {i18n._(t`Test`)}
                        </Button>
                      </div>
                    </Tooltip>
                  </RevertFormActionGroup>
                </FormColumnLayout>
                {isModalOpen && (
                  <RevertAllAlert
                    onClose={closeModal}
                    onRevertAll={handleRevertAll}
                  />
                )}
                {(testSuccess || testError) && (
                  <LoggingTestAlert
                    successResponse={testSuccess}
                    errorResponse={testError}
                    onClose={handleCloseAlert}
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

export default withI18n()(LoggingEdit);
