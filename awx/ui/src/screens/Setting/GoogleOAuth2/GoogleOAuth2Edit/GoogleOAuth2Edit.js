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
import { RevertAllAlert, RevertFormActionGroup } from '../../shared';
import {
  EncryptedField,
  InputField,
  ObjectField,
} from '../../shared/SharedFields';
import { formatJson } from '../../shared/settingUtils';

function GoogleOAuth2Edit() {
  const history = useHistory();
  const { isModalOpen, toggleModal, closeModal } = useModal();
  const { PUT: options } = useSettings();

  const {
    isLoading,
    error,
    request: fetchGoogleOAuth2,
    result: googleOAuth2,
  } = useRequest(
    useCallback(async () => {
      const { data } = await SettingsAPI.readCategory('google-oauth2');
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
    fetchGoogleOAuth2();
  }, [fetchGoogleOAuth2]);

  const { error: submitError, request: submitForm } = useRequest(
    useCallback(
      async (values) => {
        await SettingsAPI.updateAll(values);
        history.push('/settings/google_oauth2/details');
      },
      [history]
    ),
    null
  );

  const { error: revertError, request: revertAll } = useRequest(
    useCallback(async () => {
      await SettingsAPI.revertCategory('google-oauth2');
    }, []),
    null
  );

  const handleSubmit = async (form) => {
    await submitForm({
      ...form,
      SOCIAL_AUTH_GOOGLE_OAUTH2_WHITELISTED_DOMAINS: formatJson(
        form.SOCIAL_AUTH_GOOGLE_OAUTH2_WHITELISTED_DOMAINS
      ),
      SOCIAL_AUTH_GOOGLE_OAUTH2_AUTH_EXTRA_ARGUMENTS: formatJson(
        form.SOCIAL_AUTH_GOOGLE_OAUTH2_AUTH_EXTRA_ARGUMENTS
      ),
      SOCIAL_AUTH_GOOGLE_OAUTH2_ORGANIZATION_MAP: formatJson(
        form.SOCIAL_AUTH_GOOGLE_OAUTH2_ORGANIZATION_MAP
      ),
      SOCIAL_AUTH_GOOGLE_OAUTH2_TEAM_MAP: formatJson(
        form.SOCIAL_AUTH_GOOGLE_OAUTH2_TEAM_MAP
      ),
    });
  };

  const handleRevertAll = async () => {
    await revertAll();

    closeModal();

    history.push('/settings/google_oauth2/details');
  };

  const handleCancel = () => {
    history.push('/settings/google_oauth2/details');
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
      {!isLoading && googleOAuth2 && (
        <Formik
          initialValues={initialValues(googleOAuth2)}
          onSubmit={handleSubmit}
        >
          {(formik) => (
            <Form autoComplete="off" onSubmit={formik.handleSubmit}>
              <FormColumnLayout>
                <InputField
                  name="SOCIAL_AUTH_GOOGLE_OAUTH2_KEY"
                  config={googleOAuth2.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY}
                />
                <EncryptedField
                  name="SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET"
                  config={googleOAuth2.SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET}
                />
                <ObjectField
                  name="SOCIAL_AUTH_GOOGLE_OAUTH2_WHITELISTED_DOMAINS"
                  config={
                    googleOAuth2.SOCIAL_AUTH_GOOGLE_OAUTH2_WHITELISTED_DOMAINS
                  }
                />
                <ObjectField
                  name="SOCIAL_AUTH_GOOGLE_OAUTH2_AUTH_EXTRA_ARGUMENTS"
                  config={
                    googleOAuth2.SOCIAL_AUTH_GOOGLE_OAUTH2_AUTH_EXTRA_ARGUMENTS
                  }
                />
                <ObjectField
                  name="SOCIAL_AUTH_GOOGLE_OAUTH2_ORGANIZATION_MAP"
                  config={
                    googleOAuth2.SOCIAL_AUTH_GOOGLE_OAUTH2_ORGANIZATION_MAP
                  }
                />
                <ObjectField
                  name="SOCIAL_AUTH_GOOGLE_OAUTH2_TEAM_MAP"
                  config={googleOAuth2.SOCIAL_AUTH_GOOGLE_OAUTH2_TEAM_MAP}
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

export default GoogleOAuth2Edit;
