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

function GitHubEnterpriseTeamEdit() {
  const history = useHistory();
  const { isModalOpen, toggleModal, closeModal } = useModal();
  const { PUT: options } = useSettings();

  const {
    isLoading,
    error,
    request: fetchGithub,
    result: github,
  } = useRequest(
    useCallback(async () => {
      const { data } = await SettingsAPI.readCategory('github-enterprise-team');
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
    fetchGithub();
  }, [fetchGithub]);

  const { error: submitError, request: submitForm } = useRequest(
    useCallback(
      async (values) => {
        await SettingsAPI.updateAll(values);
        history.push('/settings/github/enterprise_team/details');
      },
      [history]
    ),
    null
  );

  const { error: revertError, request: revertAll } = useRequest(
    useCallback(async () => {
      await SettingsAPI.revertCategory('github-enterprise-team');
    }, []),
    null
  );

  const handleSubmit = async (form) => {
    await submitForm({
      ...form,
      SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_ORGANIZATION_MAP: formatJson(
        form.SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_ORGANIZATION_MAP
      ),
      SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_TEAM_MAP: formatJson(
        form.SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_TEAM_MAP
      ),
    });
  };

  const handleRevertAll = async () => {
    await revertAll();

    closeModal();

    history.push('/settings/github/enterprise_team/details');
  };

  const handleCancel = () => {
    history.push('/settings/github/enterprise_team/details');
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
      {!isLoading && github && (
        <Formik initialValues={initialValues(github)} onSubmit={handleSubmit}>
          {(formik) => (
            <Form autoComplete="off" onSubmit={formik.handleSubmit}>
              <FormColumnLayout>
                <InputField
                  name="SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_URL"
                  config={github.SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_URL}
                />
                <InputField
                  name="SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_API_URL"
                  config={github.SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_API_URL}
                />
                <InputField
                  name="SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_KEY"
                  config={github.SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_KEY}
                />
                <EncryptedField
                  name="SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_SECRET"
                  config={github.SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_SECRET}
                />
                <InputField
                  name="SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_ID"
                  config={github.SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_ID}
                />
                <ObjectField
                  name="SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_ORGANIZATION_MAP"
                  config={
                    github.SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_ORGANIZATION_MAP
                  }
                />
                <ObjectField
                  name="SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_TEAM_MAP"
                  config={github.SOCIAL_AUTH_GITHUB_ENTERPRISE_TEAM_TEAM_MAP}
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

export default GitHubEnterpriseTeamEdit;
