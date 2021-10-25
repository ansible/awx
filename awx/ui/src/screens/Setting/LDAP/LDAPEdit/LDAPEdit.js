import React, { useCallback, useEffect } from 'react';
import { useHistory, useRouteMatch } from 'react-router-dom';
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
import { RevertAllAlert, RevertFormActionGroup } from '../../shared';
import {
  BooleanField,
  ChoiceField,
  EncryptedField,
  InputField,
  ObjectField,
} from '../../shared/SharedFields';
import { formatJson } from '../../shared/settingUtils';

function filterByPrefix(data, prefix) {
  return Object.keys(data)
    .filter((key) => key.includes(prefix))
    .reduce((obj, key) => {
      obj[key] = data[key];
      return obj;
    }, {});
}

function LDAPEdit() {
  const history = useHistory();
  const { isModalOpen, toggleModal, closeModal } = useModal();
  const { PUT: options } = useSettings();
  const {
    params: { category },
  } = useRouteMatch('/settings/ldap/:category/edit');
  const ldapCategory =
    category === 'default' ? 'AUTH_LDAP_' : `AUTH_LDAP_${category}_`;

  const {
    isLoading,
    error,
    request: fetchLDAP,
    result: ldap,
  } = useRequest(
    useCallback(async () => {
      const { data } = await SettingsAPI.readCategory('ldap');

      const mergedData = {};
      Object.keys(data).forEach((key) => {
        if (!options[key]) {
          return;
        }
        mergedData[key] = options[key];
        mergedData[key].value = data[key];
      });

      const allCategories = {
        AUTH_LDAP_1_: filterByPrefix(mergedData, 'AUTH_LDAP_1_'),
        AUTH_LDAP_2_: filterByPrefix(mergedData, 'AUTH_LDAP_2_'),
        AUTH_LDAP_3_: filterByPrefix(mergedData, 'AUTH_LDAP_3_'),
        AUTH_LDAP_4_: filterByPrefix(mergedData, 'AUTH_LDAP_4_'),
        AUTH_LDAP_5_: filterByPrefix(mergedData, 'AUTH_LDAP_5_'),
        AUTH_LDAP_: { ...mergedData },
      };
      Object.keys({
        ...allCategories.AUTH_LDAP_1_,
        ...allCategories.AUTH_LDAP_2_,
        ...allCategories.AUTH_LDAP_3_,
        ...allCategories.AUTH_LDAP_4_,
        ...allCategories.AUTH_LDAP_5_,
      }).forEach((keyToOmit) => {
        delete allCategories.AUTH_LDAP_[keyToOmit];
      });

      return allCategories[ldapCategory];
    }, [options, ldapCategory]),
    null
  );

  useEffect(() => {
    fetchLDAP();
  }, [fetchLDAP]);

  const { error: submitError, request: submitForm } = useRequest(
    useCallback(
      async (values) => {
        await SettingsAPI.updateAll(values);
        history.push(`/settings/ldap/${category}/details`);
      },
      [history, category]
    ),
    null
  );

  const handleSubmit = async (form) => {
    await submitForm({
      [`${ldapCategory}BIND_DN`]: form[`${ldapCategory}BIND_DN`],
      [`${ldapCategory}BIND_PASSWORD`]: form[`${ldapCategory}BIND_PASSWORD`],
      [`${ldapCategory}DENY_GROUP`]: form[`${ldapCategory}DENY_GROUP`],
      [`${ldapCategory}GROUP_TYPE`]: form[`${ldapCategory}GROUP_TYPE`],
      [`${ldapCategory}REQUIRE_GROUP`]: form[`${ldapCategory}REQUIRE_GROUP`],
      [`${ldapCategory}SERVER_URI`]: form[`${ldapCategory}SERVER_URI`],
      [`${ldapCategory}START_TLS`]: form[`${ldapCategory}START_TLS`],
      [`${ldapCategory}USER_DN_TEMPLATE`]:
        form[`${ldapCategory}USER_DN_TEMPLATE`],
      [`${ldapCategory}GROUP_SEARCH`]: formatJson(
        form[`${ldapCategory}GROUP_SEARCH`]
      ),
      [`${ldapCategory}GROUP_TYPE_PARAMS`]: formatJson(
        form[`${ldapCategory}GROUP_TYPE_PARAMS`]
      ),
      [`${ldapCategory}ORGANIZATION_MAP`]: formatJson(
        form[`${ldapCategory}ORGANIZATION_MAP`]
      ),
      [`${ldapCategory}TEAM_MAP`]: formatJson(form[`${ldapCategory}TEAM_MAP`]),
      [`${ldapCategory}USER_ATTR_MAP`]: formatJson(
        form[`${ldapCategory}USER_ATTR_MAP`]
      ),
      [`${ldapCategory}USER_FLAGS_BY_GROUP`]: formatJson(
        form[`${ldapCategory}USER_FLAGS_BY_GROUP`]
      ),
      [`${ldapCategory}USER_SEARCH`]: formatJson(
        form[`${ldapCategory}USER_SEARCH`]
      ),
    });
  };

  const handleRevertAll = async () => {
    const defaultValues = Object.assign(
      ...Object.entries(ldap).map(([key, value]) => ({
        [key]: value.default,
      }))
    );
    await submitForm(defaultValues);
    closeModal();
  };

  const handleCancel = () => {
    history.push(`/settings/ldap/${category}/details`);
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
      {!isLoading && ldap && (
        <Formik initialValues={initialValues(ldap)} onSubmit={handleSubmit}>
          {(formik) => (
            <Form autoComplete="off" onSubmit={formik.handleSubmit}>
              <FormColumnLayout>
                <InputField
                  name={`${ldapCategory}SERVER_URI`}
                  config={ldap[`${ldapCategory}SERVER_URI`]}
                />
                <EncryptedField
                  name={`${ldapCategory}BIND_PASSWORD`}
                  config={ldap[`${ldapCategory}BIND_PASSWORD`]}
                />
                <ChoiceField
                  name={`${ldapCategory}GROUP_TYPE`}
                  config={ldap[`${ldapCategory}GROUP_TYPE`]}
                />
                <BooleanField
                  name={`${ldapCategory}START_TLS`}
                  config={ldap[`${ldapCategory}START_TLS`]}
                />
                <FormFullWidthLayout>
                  <InputField
                    name={`${ldapCategory}BIND_DN`}
                    config={ldap[`${ldapCategory}BIND_DN`]}
                  />
                  <InputField
                    name={`${ldapCategory}USER_DN_TEMPLATE`}
                    config={ldap[`${ldapCategory}USER_DN_TEMPLATE`]}
                  />
                  <InputField
                    name={`${ldapCategory}REQUIRE_GROUP`}
                    config={ldap[`${ldapCategory}REQUIRE_GROUP`]}
                  />
                  <InputField
                    name={`${ldapCategory}DENY_GROUP`}
                    config={ldap[`${ldapCategory}DENY_GROUP`]}
                  />
                </FormFullWidthLayout>
                <ObjectField
                  name={`${ldapCategory}USER_SEARCH`}
                  config={ldap[`${ldapCategory}USER_SEARCH`]}
                />
                <ObjectField
                  name={`${ldapCategory}GROUP_SEARCH`}
                  config={ldap[`${ldapCategory}GROUP_SEARCH`]}
                />
                <ObjectField
                  name={`${ldapCategory}USER_ATTR_MAP`}
                  config={ldap[`${ldapCategory}USER_ATTR_MAP`]}
                />
                <ObjectField
                  name={`${ldapCategory}GROUP_TYPE_PARAMS`}
                  config={ldap[`${ldapCategory}GROUP_TYPE_PARAMS`]}
                />
                <ObjectField
                  name={`${ldapCategory}USER_FLAGS_BY_GROUP`}
                  config={ldap[`${ldapCategory}USER_FLAGS_BY_GROUP`]}
                />
                <ObjectField
                  name={`${ldapCategory}ORGANIZATION_MAP`}
                  config={ldap[`${ldapCategory}ORGANIZATION_MAP`]}
                />
                <ObjectField
                  name={`${ldapCategory}TEAM_MAP`}
                  config={ldap[`${ldapCategory}TEAM_MAP`]}
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

export default LDAPEdit;
