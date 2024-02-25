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
import { SettingsAPI, ExecutionEnvironmentsAPI } from 'api';
import {
  BooleanField,
  EncryptedField,
  ExecutionEnvField,
  InputField,
  ObjectField,
  RevertAllAlert,
  RevertFormActionGroup,
} from '../../shared';
import { pluck, formatJson } from '../../shared/settingUtils';

function MiscSystemEdit() {
  const history = useHistory();
  const { isModalOpen, toggleModal, closeModal } = useModal();
  const { PUT: options } = useSettings();

  const {
    isLoading,
    error,
    request: fetchSystem,
    result: system,
  } = useRequest(
    useCallback(async () => {
      const { data } = await SettingsAPI.readCategory('system');
      const systemData = pluck(
        data,
        'ACTIVITY_STREAM_ENABLED',
        'ACTIVITY_STREAM_ENABLED_FOR_INVENTORY_SYNC',
        'AUTOMATION_ANALYTICS_GATHER_INTERVAL',
        'AUTOMATION_ANALYTICS_URL',
        'AUTOMATION_ANALYTICS_LAST_ENTRIES',
        'INSIGHTS_TRACKING_STATE',
        'MANAGE_ORGANIZATION_AUTH',
        'ORG_ADMINS_CAN_SEE_ALL_USERS',
        'REDHAT_USERNAME',
        'REDHAT_PASSWORD',
        'SUBSCRIPTIONS_USERNAME',
        'SUBSCRIPTIONS_PASSWORD',
        'REMOTE_HOST_HEADERS',
        'TOWER_URL_BASE',
        'DEFAULT_EXECUTION_ENVIRONMENT',
        'PROXY_IP_ALLOWED_LIST',
        'CSRF_TRUSTED_ORIGINS',
        'UI_NEXT'
      );

      const mergedData = {};
      Object.keys(systemData).forEach((key) => {
        if (!options[key]) {
          return;
        }
        mergedData[key] = options[key];
        mergedData[key].value = systemData[key];
      });
      return mergedData;
    }, [options]),
    null
  );

  useEffect(() => {
    fetchSystem();
  }, [fetchSystem]);

  const { error: submitError, request: submitForm } = useRequest(
    useCallback(
      async (values) => {
        await SettingsAPI.updateAll(values);
        history.push('/settings/miscellaneous_system/details');
      },
      [history]
    ),
    null
  );

  const { error: revertError, request: revertAll } = useRequest(
    useCallback(async () => {
      await SettingsAPI.revertCategory('system');
    }, []),
    null
  );

  const handleSubmit = async (form) => {
    await submitForm({
      ...form,
      PROXY_IP_ALLOWED_LIST: formatJson(form.PROXY_IP_ALLOWED_LIST),
      CSRF_TRUSTED_ORIGINS: formatJson(form.CSRF_TRUSTED_ORIGINS),
      REMOTE_HOST_HEADERS: formatJson(form.REMOTE_HOST_HEADERS),
      DEFAULT_EXECUTION_ENVIRONMENT:
        form.DEFAULT_EXECUTION_ENVIRONMENT?.id || null,
    });
  };

  const handleRevertAll = async () => {
    await revertAll();

    closeModal();

    history.push('/settings/miscellaneous_system/details');
  };

  const handleCancel = () => {
    history.push('/settings/miscellaneous_system/details');
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

  const executionEnvironmentId =
    system?.DEFAULT_EXECUTION_ENVIRONMENT?.value || null;

  const {
    isLoading: isLoadingExecutionEnvironment,
    error: errorExecutionEnvironment,
    request: fetchExecutionEnvironment,
    result: executionEnvironment,
  } = useRequest(
    useCallback(async () => {
      if (!executionEnvironmentId) {
        return '';
      }
      const { data } = await ExecutionEnvironmentsAPI.readDetail(
        executionEnvironmentId
      );
      return data;
    }, [executionEnvironmentId])
  );

  useEffect(() => {
    fetchExecutionEnvironment();
  }, [fetchExecutionEnvironment]);

  return (
    <CardBody>
      {(isLoading || isLoadingExecutionEnvironment) && <ContentLoading />}
      {!(isLoading || isLoadingExecutionEnvironment) && error && (
        <ContentError error={error || errorExecutionEnvironment} />
      )}
      {!(isLoading || isLoadingExecutionEnvironment) && system && (
        <Formik
          initialValues={{
            ...initialValues(system),
            DEFAULT_EXECUTION_ENVIRONMENT: executionEnvironment
              ? { id: executionEnvironment.id, name: executionEnvironment.name }
              : null,
          }}
          onSubmit={handleSubmit}
        >
          {(formik) => (
            <Form autoComplete="off" onSubmit={formik.handleSubmit}>
              <FormColumnLayout>
                <BooleanField
                  name="ACTIVITY_STREAM_ENABLED"
                  config={system.ACTIVITY_STREAM_ENABLED}
                />
                <BooleanField
                  name="ACTIVITY_STREAM_ENABLED_FOR_INVENTORY_SYNC"
                  config={system.ACTIVITY_STREAM_ENABLED_FOR_INVENTORY_SYNC}
                />
                <ExecutionEnvField
                  name="DEFAULT_EXECUTION_ENVIRONMENT"
                  config={system.DEFAULT_EXECUTION_ENVIRONMENT}
                />
                <InputField
                  name="TOWER_URL_BASE"
                  config={system.TOWER_URL_BASE}
                  isRequired
                  type="url"
                />
                <BooleanField
                  name="ORG_ADMINS_CAN_SEE_ALL_USERS"
                  config={system.ORG_ADMINS_CAN_SEE_ALL_USERS}
                />
                <BooleanField
                  name="MANAGE_ORGANIZATION_AUTH"
                  config={system.MANAGE_ORGANIZATION_AUTH}
                />
                <BooleanField
                  name="INSIGHTS_TRACKING_STATE"
                  config={system.INSIGHTS_TRACKING_STATE}
                />
                <InputField
                  name="REDHAT_USERNAME"
                  config={system.REDHAT_USERNAME}
                />
                <EncryptedField
                  name="REDHAT_PASSWORD"
                  config={system.REDHAT_PASSWORD}
                />
                <InputField
                  name="SUBSCRIPTIONS_USERNAME"
                  config={system.SUBSCRIPTIONS_USERNAME}
                />
                <EncryptedField
                  name="SUBSCRIPTIONS_PASSWORD"
                  config={system.SUBSCRIPTIONS_PASSWORD}
                />
                <InputField
                  name="AUTOMATION_ANALYTICS_URL"
                  config={system.AUTOMATION_ANALYTICS_URL}
                  type="url"
                />
                <InputField
                  name="AUTOMATION_ANALYTICS_GATHER_INTERVAL"
                  config={system.AUTOMATION_ANALYTICS_GATHER_INTERVAL}
                  type="number"
                  isRequired
                />
                <BooleanField name="UI_NEXT" config={system.UI_NEXT} />
                <ObjectField
                  name="AUTOMATION_ANALYTICS_LAST_ENTRIES"
                  config={system.AUTOMATION_ANALYTICS_LAST_ENTRIES}
                  revertValue={system.AUTOMATION_ANALYTICS_LAST_ENTRIES.default}
                />
                <ObjectField
                  name="REMOTE_HOST_HEADERS"
                  config={system.REMOTE_HOST_HEADERS}
                  isRequired
                />
                <ObjectField
                  name="PROXY_IP_ALLOWED_LIST"
                  config={system.PROXY_IP_ALLOWED_LIST}
                  isRequired
                />
                <ObjectField
                  name="CSRF_TRUSTED_ORIGINS"
                  config={system.CSRF_TRUSTED_ORIGINS}
                  isRequired
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

export default MiscSystemEdit;
