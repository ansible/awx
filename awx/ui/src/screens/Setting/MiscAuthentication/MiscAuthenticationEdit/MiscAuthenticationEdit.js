import React, { useCallback, useEffect } from 'react';
import { useHistory } from 'react-router-dom';
import { t } from '@lingui/macro';
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
  InputField,
  ObjectField,
  InputAlertField,
} from '../../shared/SharedFields';
import { RevertAllAlert, RevertFormActionGroup } from '../../shared';
import { formatJson, pluck } from '../../shared/settingUtils';

function MiscAuthenticationEdit() {
  const history = useHistory();
  const { isModalOpen, toggleModal, closeModal } = useModal();
  const { PUT: options } = useSettings();

  const {
    isLoading,
    error,
    request: fetchAuthentication,
    result: authentication,
  } = useRequest(
    useCallback(async () => {
      const { data } = await SettingsAPI.readCategory('authentication');

      const {
        OAUTH2_PROVIDER: {
          ACCESS_TOKEN_EXPIRE_SECONDS,
          REFRESH_TOKEN_EXPIRE_SECONDS,
          AUTHORIZATION_CODE_EXPIRE_SECONDS,
        },
        ...pluckedAuthenticationData
      } = pluck(
        data,
        'ALLOW_OAUTH2_FOR_EXTERNAL_USERS',
        'AUTH_BASIC_ENABLED',
        'LOGIN_REDIRECT_OVERRIDE',
        'DISABLE_LOCAL_AUTH',
        'OAUTH2_PROVIDER',
        'SESSIONS_PER_USER',
        'SESSION_COOKIE_AGE',
        'SOCIAL_AUTH_ORGANIZATION_MAP',
        'SOCIAL_AUTH_TEAM_MAP',
        'SOCIAL_AUTH_USER_FIELDS',
        'SOCIAL_AUTH_USERNAME_IS_FULL_EMAIL',
        'LOCAL_PASSWORD_MIN_LENGTH',
        'LOCAL_PASSWORD_MIN_DIGITS',
        'LOCAL_PASSWORD_MIN_UPPER',
        'LOCAL_PASSWORD_MIN_SPECIAL'
      );

      const authenticationData = {
        ACCESS_TOKEN_EXPIRE_SECONDS,
        REFRESH_TOKEN_EXPIRE_SECONDS,
        AUTHORIZATION_CODE_EXPIRE_SECONDS,
        ...pluckedAuthenticationData,
      };

      const { OAUTH2_PROVIDER: OAUTH2_PROVIDER_OPTIONS, ...restOptions } =
        options;

      const authenticationOptions = {
        ...restOptions,
        ACCESS_TOKEN_EXPIRE_SECONDS: {
          ...OAUTH2_PROVIDER_OPTIONS,
          default: OAUTH2_PROVIDER_OPTIONS.default.ACCESS_TOKEN_EXPIRE_SECONDS,
          type: OAUTH2_PROVIDER_OPTIONS.child.type,
          label: t`Access Token Expiration`,
        },
        REFRESH_TOKEN_EXPIRE_SECONDS: {
          ...OAUTH2_PROVIDER_OPTIONS,
          default: OAUTH2_PROVIDER_OPTIONS.default.REFRESH_TOKEN_EXPIRE_SECONDS,
          type: OAUTH2_PROVIDER_OPTIONS.child.type,
          label: t`Refresh Token Expiration`,
        },
        AUTHORIZATION_CODE_EXPIRE_SECONDS: {
          ...OAUTH2_PROVIDER_OPTIONS,
          default:
            OAUTH2_PROVIDER_OPTIONS.default.AUTHORIZATION_CODE_EXPIRE_SECONDS,
          type: OAUTH2_PROVIDER_OPTIONS.child.type,
          label: t`Authorization Code Expiration`,
        },
      };

      const mergedData = {};

      Object.keys(authenticationData).forEach((key) => {
        if (!authenticationOptions[key]) {
          return;
        }
        mergedData[key] = authenticationOptions[key];
        mergedData[key].value = authenticationData[key];
      });

      return mergedData;
    }, [options]),
    null
  );

  useEffect(() => {
    fetchAuthentication();
  }, [fetchAuthentication]);

  const { error: submitError, request: submitForm } = useRequest(
    useCallback(
      async (values) => {
        await SettingsAPI.updateAll(values);
        history.push('/settings/miscellaneous_authentication/details');
      },
      [history]
    ),
    null
  );

  const { error: revertError, request: revertAll } = useRequest(
    useCallback(async () => {
      await SettingsAPI.revertCategory('authentication');
    }, []),
    null
  );

  const handleSubmit = async (form) => {
    const {
      ACCESS_TOKEN_EXPIRE_SECONDS,
      REFRESH_TOKEN_EXPIRE_SECONDS,
      AUTHORIZATION_CODE_EXPIRE_SECONDS,
      ...formData
    } = form;

    await submitForm({
      ...formData,
      OAUTH2_PROVIDER: {
        ACCESS_TOKEN_EXPIRE_SECONDS,
        REFRESH_TOKEN_EXPIRE_SECONDS,
        AUTHORIZATION_CODE_EXPIRE_SECONDS,
      },
      SOCIAL_AUTH_ORGANIZATION_MAP: formatJson(
        formData.SOCIAL_AUTH_ORGANIZATION_MAP
      ),
      SOCIAL_AUTH_TEAM_MAP: formatJson(formData.SOCIAL_AUTH_TEAM_MAP),
      SOCIAL_AUTH_USER_FIELDS: formatJson(formData.SOCIAL_AUTH_USER_FIELDS),
    });
  };

  const handleRevertAll = async () => {
    await revertAll();

    closeModal();

    history.push('/settings/miscellaneous_authentication/details');
  };

  const handleCancel = () => {
    history.push('/settings/miscellaneous_authentication/details');
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
      {!isLoading && authentication && (
        <Formik
          initialValues={initialValues(authentication)}
          onSubmit={handleSubmit}
        >
          {(formik) => (
            <Form autoComplete="off" onSubmit={formik.handleSubmit}>
              <FormColumnLayout>
                <BooleanField
                  name="DISABLE_LOCAL_AUTH"
                  needsConfirmationModal
                  modalTitle={t`Confirm Disable Local Authorization`}
                  config={authentication.DISABLE_LOCAL_AUTH}
                />
                <InputField
                  name="SESSION_COOKIE_AGE"
                  config={authentication.SESSION_COOKIE_AGE}
                  type="number"
                  isRequired
                />
                <InputField
                  name="SESSIONS_PER_USER"
                  config={authentication.SESSIONS_PER_USER}
                  type="number"
                  isRequired
                />
                <BooleanField
                  name="AUTH_BASIC_ENABLED"
                  config={authentication.AUTH_BASIC_ENABLED}
                />
                <BooleanField
                  name="ALLOW_OAUTH2_FOR_EXTERNAL_USERS"
                  config={authentication.ALLOW_OAUTH2_FOR_EXTERNAL_USERS}
                />
                <InputAlertField
                  name="LOGIN_REDIRECT_OVERRIDE"
                  config={authentication.LOGIN_REDIRECT_OVERRIDE}
                />
                <InputField
                  name="ACCESS_TOKEN_EXPIRE_SECONDS"
                  config={authentication.ACCESS_TOKEN_EXPIRE_SECONDS}
                  type="number"
                />
                <InputField
                  name="REFRESH_TOKEN_EXPIRE_SECONDS"
                  config={authentication.REFRESH_TOKEN_EXPIRE_SECONDS}
                  type="number"
                />
                <InputField
                  name="AUTHORIZATION_CODE_EXPIRE_SECONDS"
                  config={authentication.AUTHORIZATION_CODE_EXPIRE_SECONDS}
                  type="number"
                />
                <ObjectField
                  name="SOCIAL_AUTH_ORGANIZATION_MAP"
                  config={authentication.SOCIAL_AUTH_ORGANIZATION_MAP}
                />
                <ObjectField
                  name="SOCIAL_AUTH_TEAM_MAP"
                  config={authentication.SOCIAL_AUTH_TEAM_MAP}
                />
                <ObjectField
                  name="SOCIAL_AUTH_USER_FIELDS"
                  config={authentication.SOCIAL_AUTH_USER_FIELDS}
                />
                <BooleanField
                  name="SOCIAL_AUTH_USERNAME_IS_FULL_EMAIL"
                  config={authentication.SOCIAL_AUTH_USERNAME_IS_FULL_EMAIL}
                />
                <InputField
                  name="LOCAL_PASSWORD_MIN_LENGTH"
                  config={authentication.LOCAL_PASSWORD_MIN_LENGTH}
                  type="number"
                  isRequired
                />
                <InputField
                  name="LOCAL_PASSWORD_MIN_DIGITS"
                  config={authentication.LOCAL_PASSWORD_MIN_DIGITS}
                  type="number"
                  isRequired
                />
                <InputField
                  name="LOCAL_PASSWORD_MIN_UPPER"
                  config={authentication.LOCAL_PASSWORD_MIN_UPPER}
                  type="number"
                  isRequired
                />
                <InputField
                  name="LOCAL_PASSWORD_MIN_SPECIAL"
                  config={authentication.LOCAL_PASSWORD_MIN_SPECIAL}
                  type="number"
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

export default MiscAuthenticationEdit;
