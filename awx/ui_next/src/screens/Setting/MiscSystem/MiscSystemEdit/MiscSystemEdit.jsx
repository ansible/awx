import React, { useCallback, useEffect } from 'react';
import { useHistory } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
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
  EncryptedField,
  InputField,
  ObjectField,
  RevertAllAlert,
  RevertFormActionGroup,
} from '../../shared';
import useModal from '../../../../util/useModal';
import useRequest from '../../../../util/useRequest';
import { SettingsAPI } from '../../../../api';
import { pluck, formatJson } from '../../shared/settingUtils';

function MiscSystemEdit({ i18n }) {
  const history = useHistory();
  const { isModalOpen, toggleModal, closeModal } = useModal();
  const { PUT: options } = useSettings();

  const { isLoading, error, request: fetchSystem, result: system } = useRequest(
    useCallback(async () => {
      const { data } = await SettingsAPI.readCategory('all');
      const {
        OAUTH2_PROVIDER: {
          ACCESS_TOKEN_EXPIRE_SECONDS,
          REFRESH_TOKEN_EXPIRE_SECONDS,
          AUTHORIZATION_CODE_EXPIRE_SECONDS,
        },
        ...pluckedSystemData
      } = pluck(
        data,
        'ALLOW_OAUTH2_FOR_EXTERNAL_USERS',
        'AUTH_BASIC_ENABLED',
        'AUTOMATION_ANALYTICS_GATHER_INTERVAL',
        'AUTOMATION_ANALYTICS_URL',
        'CUSTOM_VENV_PATHS',
        'INSIGHTS_TRACKING_STATE',
        'LOGIN_REDIRECT_OVERRIDE',
        'MANAGE_ORGANIZATION_AUTH',
        'OAUTH2_PROVIDER',
        'ORG_ADMINS_CAN_SEE_ALL_USERS',
        'REDHAT_PASSWORD',
        'REDHAT_USERNAME',
        'REMOTE_HOST_HEADERS',
        'SESSIONS_PER_USER',
        'SESSION_COOKIE_AGE',
        'TOWER_URL_BASE'
      );

      const systemData = {
        ...pluckedSystemData,
        ACCESS_TOKEN_EXPIRE_SECONDS,
        REFRESH_TOKEN_EXPIRE_SECONDS,
        AUTHORIZATION_CODE_EXPIRE_SECONDS,
      };

      const {
        OAUTH2_PROVIDER: OAUTH2_PROVIDER_OPTIONS,
        ...restOptions
      } = options;

      const systemOptions = {
        ...restOptions,
        ACCESS_TOKEN_EXPIRE_SECONDS: {
          ...OAUTH2_PROVIDER_OPTIONS,
          default: OAUTH2_PROVIDER_OPTIONS.default.ACCESS_TOKEN_EXPIRE_SECONDS,
          type: OAUTH2_PROVIDER_OPTIONS.child.type,
          label: i18n._(t`Access Token Expiration`),
        },
        REFRESH_TOKEN_EXPIRE_SECONDS: {
          ...OAUTH2_PROVIDER_OPTIONS,
          default: OAUTH2_PROVIDER_OPTIONS.default.REFRESH_TOKEN_EXPIRE_SECONDS,
          type: OAUTH2_PROVIDER_OPTIONS.child.type,
          label: i18n._(t`Refresh Token Expiration`),
        },
        AUTHORIZATION_CODE_EXPIRE_SECONDS: {
          ...OAUTH2_PROVIDER_OPTIONS,
          default:
            OAUTH2_PROVIDER_OPTIONS.default.AUTHORIZATION_CODE_EXPIRE_SECONDS,
          type: OAUTH2_PROVIDER_OPTIONS.child.type,
          label: i18n._(t`Authorization Code Expiration`),
        },
      };

      const mergedData = {};
      Object.keys(systemData).forEach(key => {
        if (!systemOptions[key]) {
          return;
        }
        mergedData[key] = systemOptions[key];
        mergedData[key].value = systemData[key];
      });
      return mergedData;
    }, [options, i18n]),
    null
  );

  useEffect(() => {
    fetchSystem();
  }, [fetchSystem]);

  const { error: submitError, request: submitForm } = useRequest(
    useCallback(
      async values => {
        await SettingsAPI.updateAll(values);
        history.push('/settings/miscellaneous_system/details');
      },
      [history]
    ),
    null
  );

  const handleSubmit = async form => {
    const {
      ACCESS_TOKEN_EXPIRE_SECONDS,
      REFRESH_TOKEN_EXPIRE_SECONDS,
      AUTHORIZATION_CODE_EXPIRE_SECONDS,
      ...formData
    } = form;
    await submitForm({
      ...formData,
      CUSTOM_VENV_PATHS: formatJson(formData.CUSTOM_VENV_PATHS),
      REMOTE_HOST_HEADERS: formatJson(formData.REMOTE_HOST_HEADERS),
      OAUTH2_PROVIDER: {
        ACCESS_TOKEN_EXPIRE_SECONDS,
        REFRESH_TOKEN_EXPIRE_SECONDS,
        AUTHORIZATION_CODE_EXPIRE_SECONDS,
      },
    });
  };

  const handleRevertAll = async () => {
    const {
      ACCESS_TOKEN_EXPIRE_SECONDS,
      REFRESH_TOKEN_EXPIRE_SECONDS,
      AUTHORIZATION_CODE_EXPIRE_SECONDS,
      ...systemData
    } = system;

    const defaultValues = {};
    Object.entries(systemData).forEach(([key, value]) => {
      defaultValues[key] = value.default;
    });

    await submitForm({
      ...defaultValues,
      OAUTH2_PROVIDER: {
        ACCESS_TOKEN_EXPIRE_SECONDS: ACCESS_TOKEN_EXPIRE_SECONDS.default,
        REFRESH_TOKEN_EXPIRE_SECONDS: REFRESH_TOKEN_EXPIRE_SECONDS.default,
        AUTHORIZATION_CODE_EXPIRE_SECONDS:
          AUTHORIZATION_CODE_EXPIRE_SECONDS.default,
      },
    });
    closeModal();
  };

  const handleCancel = () => {
    history.push('/settings/miscellaneous_system/details');
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
      {!isLoading && system && (
        <Formik initialValues={initialValues(system)} onSubmit={handleSubmit}>
          {formik => {
            return (
              <Form autoComplete="off" onSubmit={formik.handleSubmit}>
                <FormColumnLayout>
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
                  <InputField
                    name="SESSION_COOKIE_AGE"
                    config={system.SESSION_COOKIE_AGE}
                    type="number"
                    isRequired
                  />
                  <InputField
                    name="SESSIONS_PER_USER"
                    config={system.SESSIONS_PER_USER}
                    type="number"
                    isRequired
                  />
                  <BooleanField
                    name="AUTH_BASIC_ENABLED"
                    config={system.AUTH_BASIC_ENABLED}
                  />
                  <BooleanField
                    name="ALLOW_OAUTH2_FOR_EXTERNAL_USERS"
                    config={system.ALLOW_OAUTH2_FOR_EXTERNAL_USERS}
                  />
                  <InputField
                    name="LOGIN_REDIRECT_OVERRIDE"
                    config={system.LOGIN_REDIRECT_OVERRIDE}
                    type="url"
                  />
                  <InputField
                    name="ACCESS_TOKEN_EXPIRE_SECONDS"
                    config={system.ACCESS_TOKEN_EXPIRE_SECONDS}
                    type="number"
                  />
                  <InputField
                    name="REFRESH_TOKEN_EXPIRE_SECONDS"
                    config={system.REFRESH_TOKEN_EXPIRE_SECONDS}
                    type="number"
                  />
                  <InputField
                    name="AUTHORIZATION_CODE_EXPIRE_SECONDS"
                    config={system.AUTHORIZATION_CODE_EXPIRE_SECONDS}
                    type="number"
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
                  <ObjectField
                    name="REMOTE_HOST_HEADERS"
                    config={system.REMOTE_HOST_HEADERS}
                    isRequired
                  />
                  <ObjectField
                    name="CUSTOM_VENV_PATHS"
                    config={system.CUSTOM_VENV_PATHS}
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

export default withI18n()(MiscSystemEdit);
