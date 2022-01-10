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
  BooleanField,
  FileUploadField,
  InputField,
  ObjectField,
} from '../../shared/SharedFields';
import { formatJson } from '../../shared/settingUtils';

function SAMLEdit() {
  const history = useHistory();
  const { isModalOpen, toggleModal, closeModal } = useModal();
  const { PUT: options } = useSettings();

  const {
    isLoading,
    error,
    request: fetchSAML,
    result: saml,
  } = useRequest(
    useCallback(async () => {
      const { data } = await SettingsAPI.readCategory('saml');
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
    fetchSAML();
  }, [fetchSAML]);

  const { error: submitError, request: submitForm } = useRequest(
    useCallback(
      async (values) => {
        await SettingsAPI.updateAll(values);
        history.push('/settings/saml/details');
      },
      [history]
    ),
    null
  );

  const { error: revertError, request: revertAll } = useRequest(
    useCallback(async () => {
      await SettingsAPI.revertCategory('saml');
    }, []),
    null
  );

  const handleSubmit = async (form) => {
    await submitForm({
      ...form,
      SOCIAL_AUTH_SAML_ORG_INFO: formatJson(form.SOCIAL_AUTH_SAML_ORG_INFO),
      SOCIAL_AUTH_SAML_TECHNICAL_CONTACT: formatJson(
        form.SOCIAL_AUTH_SAML_TECHNICAL_CONTACT
      ),
      SOCIAL_AUTH_SAML_SUPPORT_CONTACT: formatJson(
        form.SOCIAL_AUTH_SAML_SUPPORT_CONTACT
      ),
      SOCIAL_AUTH_SAML_ENABLED_IDPS: formatJson(
        form.SOCIAL_AUTH_SAML_ENABLED_IDPS
      ),
      SOCIAL_AUTH_SAML_ORGANIZATION_MAP: formatJson(
        form.SOCIAL_AUTH_SAML_ORGANIZATION_MAP
      ),
      SOCIAL_AUTH_SAML_ORGANIZATION_ATTR: formatJson(
        form.SOCIAL_AUTH_SAML_ORGANIZATION_ATTR
      ),
      SOCIAL_AUTH_SAML_TEAM_MAP: formatJson(form.SOCIAL_AUTH_SAML_TEAM_MAP),
      SOCIAL_AUTH_SAML_TEAM_ATTR: formatJson(form.SOCIAL_AUTH_SAML_TEAM_ATTR),
      SOCIAL_AUTH_SAML_USER_FLAGS_BY_ATTR: formatJson(
        form.SOCIAL_AUTH_SAML_USER_FLAGS_BY_ATTR
      ),
      SOCIAL_AUTH_SAML_SECURITY_CONFIG: formatJson(
        form.SOCIAL_AUTH_SAML_SECURITY_CONFIG
      ),
      SOCIAL_AUTH_SAML_SP_EXTRA: formatJson(form.SOCIAL_AUTH_SAML_SP_EXTRA),
      SOCIAL_AUTH_SAML_EXTRA_DATA: formatJson(form.SOCIAL_AUTH_SAML_EXTRA_DATA),
    });
  };

  const handleRevertAll = async () => {
    await revertAll();

    closeModal();

    history.push('/settings/saml/details');
  };

  const handleCancel = () => {
    history.push('/settings/saml/details');
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
      {!isLoading && saml && (
        <Formik initialValues={initialValues(saml)} onSubmit={handleSubmit}>
          {(formik) => (
            <Form autoComplete="off" onSubmit={formik.handleSubmit}>
              <FormColumnLayout>
                <InputField
                  name="SOCIAL_AUTH_SAML_SP_ENTITY_ID"
                  config={saml.SOCIAL_AUTH_SAML_SP_ENTITY_ID}
                  isRequired
                />
                <BooleanField
                  name="SAML_AUTO_CREATE_OBJECTS"
                  config={saml.SAML_AUTO_CREATE_OBJECTS}
                />
                <FileUploadField
                  name="SOCIAL_AUTH_SAML_SP_PUBLIC_CERT"
                  config={saml.SOCIAL_AUTH_SAML_SP_PUBLIC_CERT}
                  isRequired
                />
                <FileUploadField
                  name="SOCIAL_AUTH_SAML_SP_PRIVATE_KEY"
                  config={saml.SOCIAL_AUTH_SAML_SP_PRIVATE_KEY}
                  isRequired
                />
                <ObjectField
                  name="SOCIAL_AUTH_SAML_ORG_INFO"
                  config={saml.SOCIAL_AUTH_SAML_ORG_INFO}
                />
                <ObjectField
                  name="SOCIAL_AUTH_SAML_TECHNICAL_CONTACT"
                  config={saml.SOCIAL_AUTH_SAML_TECHNICAL_CONTACT}
                />
                <ObjectField
                  name="SOCIAL_AUTH_SAML_SUPPORT_CONTACT"
                  config={saml.SOCIAL_AUTH_SAML_SUPPORT_CONTACT}
                />
                <ObjectField
                  name="SOCIAL_AUTH_SAML_ENABLED_IDPS"
                  config={saml.SOCIAL_AUTH_SAML_ENABLED_IDPS}
                />
                <ObjectField
                  name="SOCIAL_AUTH_SAML_ORGANIZATION_MAP"
                  config={saml.SOCIAL_AUTH_SAML_ORGANIZATION_MAP}
                />
                <ObjectField
                  name="SOCIAL_AUTH_SAML_ORGANIZATION_ATTR"
                  config={saml.SOCIAL_AUTH_SAML_ORGANIZATION_ATTR}
                />
                <ObjectField
                  name="SOCIAL_AUTH_SAML_TEAM_MAP"
                  config={saml.SOCIAL_AUTH_SAML_TEAM_MAP}
                />
                <ObjectField
                  name="SOCIAL_AUTH_SAML_TEAM_ATTR"
                  config={saml.SOCIAL_AUTH_SAML_TEAM_ATTR}
                />
                <ObjectField
                  name="SOCIAL_AUTH_SAML_USER_FLAGS_BY_ATTR"
                  config={saml.SOCIAL_AUTH_SAML_USER_FLAGS_BY_ATTR}
                />
                <ObjectField
                  name="SOCIAL_AUTH_SAML_SECURITY_CONFIG"
                  config={saml.SOCIAL_AUTH_SAML_SECURITY_CONFIG}
                />
                <ObjectField
                  name="SOCIAL_AUTH_SAML_SP_EXTRA"
                  config={saml.SOCIAL_AUTH_SAML_SP_EXTRA}
                />
                <ObjectField
                  name="SOCIAL_AUTH_SAML_EXTRA_DATA"
                  config={saml.SOCIAL_AUTH_SAML_EXTRA_DATA}
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

export default SAMLEdit;
