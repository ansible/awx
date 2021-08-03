import React, { useCallback, useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import { Formik, useField, useFormikContext } from 'formik';

import { t, Trans } from '@lingui/macro';
import { Form } from '@patternfly/react-core';

import { OrganizationsAPI } from 'api';
import { useConfig } from 'contexts/Config';
import ContentError from 'components/ContentError';
import ContentLoading from 'components/ContentLoading';
import FormField, { FormSubmitError } from 'components/FormField';
import FormActionGroup from 'components/FormActionGroup/FormActionGroup';
import {
  InstanceGroupsLookup,
  ExecutionEnvironmentLookup,
} from 'components/Lookup';
import { required, minMaxValue } from 'util/validators';
import { FormColumnLayout } from 'components/FormLayout';
import CredentialLookup from 'components/Lookup/CredentialLookup';

function OrganizationFormFields({
  instanceGroups,
  setInstanceGroups,
  organizationId,
}) {
  const { license_info = {}, me = {} } = useConfig();

  const { setFieldValue } = useFormikContext();

  const [
    galaxyCredentialsField,
    galaxyCredentialsMeta,
    galaxyCredentialsHelpers,
  ] = useField('galaxy_credentials');

  const [
    executionEnvironmentField,
    executionEnvironmentMeta,
    executionEnvironmentHelpers,
  ] = useField('default_environment');

  const handleCredentialUpdate = useCallback(
    (value) => {
      setFieldValue('galaxy_credentials', value);
    },
    [setFieldValue]
  );

  return (
    <>
      <FormField
        id="org-name"
        name="name"
        type="text"
        label={t`Name`}
        validate={required(null)}
        isRequired
      />
      <FormField
        id="org-description"
        name="description"
        type="text"
        label={t`Description`}
      />
      {license_info?.license_type !== 'open' && (
        <FormField
          id="org-max_hosts"
          name="max_hosts"
          type="number"
          label={t`Max Hosts`}
          tooltip={t`The maximum number of hosts allowed to be managed by this organization.
            Value defaults to 0 which means no limit. Refer to the Ansible
            documentation for more details.`}
          validate={minMaxValue(0, Number.MAX_SAFE_INTEGER)}
          me={me}
          isDisabled={!me.is_superuser}
        />
      )}
      <InstanceGroupsLookup
        value={instanceGroups}
        onChange={setInstanceGroups}
        tooltip={t`Select the Instance Groups for this Organization to run on.`}
      />
      <ExecutionEnvironmentLookup
        helperTextInvalid={executionEnvironmentMeta.error}
        isValid={
          !executionEnvironmentMeta.touched || !executionEnvironmentMeta.error
        }
        onBlur={() => executionEnvironmentHelpers.setTouched()}
        value={executionEnvironmentField.value}
        onChange={(value) => executionEnvironmentHelpers.setValue(value)}
        popoverContent={t`The execution environment that will be used for jobs inside of this organization. This will be used a fallback when an execution environment has not been explicitly assigned at the project, job template or workflow level.`}
        globallyAvailable
        organizationId={organizationId}
        isDefaultEnvironment
        fieldName="default_environment"
      />
      <CredentialLookup
        credentialTypeNamespace="galaxy_api_token"
        label={t`Galaxy Credentials`}
        helperTextInvalid={galaxyCredentialsMeta.error}
        isValid={!galaxyCredentialsMeta.touched || !galaxyCredentialsMeta.error}
        onBlur={() => galaxyCredentialsHelpers.setTouched()}
        onChange={handleCredentialUpdate}
        value={galaxyCredentialsField.value}
        multiple
        isSelectedDraggable
        fieldName="galaxy_credentials"
        modalDescription={
          <>
            <b>
              <Trans>Selected</Trans>
            </b>
            <br />
            <Trans>
              Note: The order of these credentials sets precedence for the sync
              and lookup of the content. Select more than one to enable drag.
            </Trans>
          </>
        }
      />
    </>
  );
}

function OrganizationForm({
  organization,
  onCancel,
  onSubmit,
  submitError,
  defaultGalaxyCredential,
  ...rest
}) {
  const [contentError, setContentError] = useState(null);
  const [hasContentLoading, setHasContentLoading] = useState(true);
  const [initialInstanceGroups, setInitialInstanceGroups] = useState([]);
  const [instanceGroups, setInstanceGroups] = useState([]);

  const handleCancel = () => {
    onCancel();
  };

  const handleSubmit = (values) => {
    if (
      typeof values.max_hosts !== 'number' ||
      values.max_hosts === 'undefined'
    ) {
      values.max_hosts = 0;
    }
    onSubmit(values, instanceGroups, initialInstanceGroups);
  };

  useEffect(() => {
    (async () => {
      const { id } = organization;
      if (!id) {
        setHasContentLoading(false);
        return;
      }
      setContentError(null);
      setHasContentLoading(true);
      try {
        const {
          data: { results = [] },
        } = await OrganizationsAPI.readInstanceGroups(id);
        setInitialInstanceGroups(results);
        setInstanceGroups(results);
      } catch (error) {
        setContentError(error);
      } finally {
        setHasContentLoading(false);
      }
    })();
  }, [organization]);

  if (contentError) {
    return <ContentError error={contentError} />;
  }

  if (hasContentLoading) {
    return <ContentLoading />;
  }

  return (
    <Formik
      initialValues={{
        name: organization.name,
        description: organization.description,
        max_hosts: organization.max_hosts || '0',
        galaxy_credentials:
          organization.galaxy_credentials ||
          (defaultGalaxyCredential ? [defaultGalaxyCredential] : []),
        default_environment:
          organization.summary_fields?.default_environment || null,
      }}
      onSubmit={handleSubmit}
    >
      {(formik) => (
        <Form autoComplete="off" onSubmit={formik.handleSubmit}>
          <FormColumnLayout>
            <OrganizationFormFields
              instanceGroups={instanceGroups}
              setInstanceGroups={setInstanceGroups}
              organizationId={organization?.id || null}
              {...rest}
            />
            <FormSubmitError error={submitError} />
            <FormActionGroup
              onCancel={handleCancel}
              onSubmit={formik.handleSubmit}
            />
          </FormColumnLayout>
        </Form>
      )}
    </Formik>
  );
}

OrganizationForm.propTypes = {
  defaultGalaxyCredential: PropTypes.shape(),
  organization: PropTypes.shape(),
  onSubmit: PropTypes.func.isRequired,
  onCancel: PropTypes.func.isRequired,
  submitError: PropTypes.shape(),
};

OrganizationForm.defaultProps = {
  defaultGalaxyCredential: null,
  organization: {
    id: '',
    name: '',
    description: '',
    max_hosts: '0',
    default_environment: '',
  },
  submitError: null,
};

export { OrganizationForm as _OrganizationForm };
export default OrganizationForm;
