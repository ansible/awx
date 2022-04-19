/* eslint no-nested-ternary: 0 */
import React, { useCallback, useState, useEffect } from 'react';
import PropTypes from 'prop-types';

import { t } from '@lingui/macro';
import { Formik, useField, useFormikContext } from 'formik';
import { Form, FormGroup, Title } from '@patternfly/react-core';
import { useConfig } from 'contexts/Config';
import AnsibleSelect from 'components/AnsibleSelect';
import ContentError from 'components/ContentError';
import ContentLoading from 'components/ContentLoading';
import FormActionGroup from 'components/FormActionGroup/FormActionGroup';
import FormField, { FormSubmitError } from 'components/FormField';
import OrganizationLookup from 'components/Lookup/OrganizationLookup';
import ExecutionEnvironmentLookup from 'components/Lookup/ExecutionEnvironmentLookup';
import { CredentialTypesAPI, ProjectsAPI } from 'api';
import { required } from 'util/validators';
import { FormColumnLayout, SubFormLayout } from 'components/FormLayout';
import ProjectHelpTextStrings from './Project.helptext';
import {
  GitSubForm,
  SvnSubForm,
  ArchiveSubForm,
  InsightsSubForm,
  ManualSubForm,
} from './ProjectSubForms';

const fetchCredentials = async (credential) => {
  const [
    {
      data: {
        results: [scmCredentialType],
      },
    },
    {
      data: {
        results: [insightsCredentialType],
      },
    },
  ] = await Promise.all([
    CredentialTypesAPI.read({ kind: 'scm' }),
    CredentialTypesAPI.read({ name: 'Insights' }),
  ]);

  if (!credential) {
    return {
      scm: { typeId: scmCredentialType.id },
      insights: { typeId: insightsCredentialType.id },
    };
  }

  const { credential_type_id } = credential;
  return {
    scm: {
      typeId: scmCredentialType.id,
      value: credential_type_id === scmCredentialType.id ? credential : null,
    },
    insights: {
      typeId: insightsCredentialType.id,
      value:
        credential_type_id === insightsCredentialType.id ? credential : null,
    },
  };
};

function ProjectFormFields({
  project,
  project_base_dir,
  project_local_paths,
  formik,
  setCredentials,
  credentials,
  scmTypeOptions,
  setScmSubFormState,
  scmSubFormState,
}) {
  const scmFormFields = {
    scm_url: '',
    scm_branch: '',
    scm_refspec: '',
    credential: '',
    scm_clean: false,
    scm_delete_on_update: false,
    scm_track_submodules: false,
    scm_update_on_launch: false,
    allow_override: false,
    scm_update_cache_timeout: 0,
  };

  const { setFieldValue, setFieldTouched } = useFormikContext();

  const [scmTypeField, scmTypeMeta, scmTypeHelpers] = useField({
    name: 'scm_type',
    validate: required(t`Set a value for this field`),
  });
  const [organizationField, organizationMeta, organizationHelpers] =
    useField('organization');

  const [
    executionEnvironmentField,
    executionEnvironmentMeta,
    executionEnvironmentHelpers,
  ] = useField('default_environment');

  /* Save current scm subform field values to state */
  const saveSubFormState = (form) => {
    const currentScmFormFields = { ...scmFormFields };

    Object.keys(currentScmFormFields).forEach((label) => {
      currentScmFormFields[label] = form.values[label];
    });

    setScmSubFormState(currentScmFormFields);
  };

  /**
   * If scm type is !== the initial scm type value,
   * reset scm subform field values to defaults.
   * If scm type is === the initial scm type value,
   * reset scm subform field values to scmSubFormState.
   */
  const resetScmTypeFields = (value, form) => {
    if (form.values.scm_type === form.initialValues.scm_type) {
      saveSubFormState(formik);
    }

    Object.keys(scmFormFields).forEach((label) => {
      if (value === form.initialValues.scm_type) {
        form.setFieldValue(label, scmSubFormState[label]);
      } else {
        form.setFieldValue(label, scmFormFields[label]);
      }
      form.setFieldTouched(label, false);
    });
  };

  const handleCredentialSelection = useCallback(
    (type, value) => {
      setCredentials({
        ...credentials,
        [type]: {
          ...credentials[type],
          value,
        },
      });
    },
    [credentials, setCredentials]
  );

  const handleOrganizationUpdate = useCallback(
    (value) => {
      setFieldValue('organization', value);
      setFieldTouched('organization', true, false);
    },
    [setFieldValue, setFieldTouched]
  );

  const handleExecutionEnvironmentUpdate = useCallback(
    (value) => {
      setFieldValue('default_environment', value);
      setFieldTouched('default_environment', true, false);
    },
    [setFieldValue, setFieldTouched]
  );

  return (
    <>
      <FormField
        id="project-name"
        label={t`Name`}
        name="name"
        type="text"
        validate={required(null)}
        isRequired
      />
      <FormField
        id="project-description"
        label={t`Description`}
        name="description"
        type="text"
      />
      <OrganizationLookup
        helperTextInvalid={organizationMeta.error}
        isValid={!organizationMeta.touched || !organizationMeta.error}
        onBlur={() => organizationHelpers.setTouched()}
        onChange={handleOrganizationUpdate}
        value={organizationField.value}
        required
        autoPopulate={!project?.id}
        validate={required(t`Select a value for this field`)}
      />
      <ExecutionEnvironmentLookup
        helperTextInvalid={executionEnvironmentMeta.error}
        isValid={
          !executionEnvironmentMeta.touched || !executionEnvironmentMeta.error
        }
        onBlur={() => executionEnvironmentHelpers.setTouched()}
        value={executionEnvironmentField.value}
        popoverContent={ProjectHelpTextStrings.execution_environment}
        onChange={handleExecutionEnvironmentUpdate}
        tooltip={t`Select an organization before editing the default execution environment.`}
        globallyAvailable
        isDisabled={!organizationField.value}
        organizationId={organizationField.value?.id}
        isDefaultEnvironment
        fieldName="default_environment"
      />
      <FormGroup
        fieldId="project-scm-type"
        helperTextInvalid={scmTypeMeta.error}
        isRequired
        validated={
          !scmTypeMeta.touched || !scmTypeMeta.error ? 'default' : 'error'
        }
        label={t`Source Control Type`}
      >
        <AnsibleSelect
          {...scmTypeField}
          id="scm_type"
          data={[
            {
              value: '',
              key: '',
              label: t`Choose a Source Control Type`,
              isDisabled: true,
            },
            ...scmTypeOptions.map(([value, label]) => {
              if (value === '') {
                value = 'manual';
              }
              return {
                label,
                value,
                key: value,
              };
            }),
          ]}
          onChange={(event, value) => {
            scmTypeHelpers.setValue(value);
            resetScmTypeFields(value, formik);
          }}
        />
      </FormGroup>
      {formik.values.scm_type !== '' && (
        <SubFormLayout>
          <Title size="md" headingLevel="h4">
            {t`Type Details`}
          </Title>
          <FormColumnLayout>
            {
              {
                manual: (
                  <ManualSubForm
                    localPath={formik.initialValues.local_path}
                    project_base_dir={project_base_dir}
                    project_local_paths={project_local_paths}
                  />
                ),
                git: (
                  <GitSubForm
                    credential={credentials.scm}
                    onCredentialSelection={handleCredentialSelection}
                    scmUpdateOnLaunch={formik.values.scm_update_on_launch}
                  />
                ),
                svn: (
                  <SvnSubForm
                    credential={credentials.scm}
                    onCredentialSelection={handleCredentialSelection}
                    scmUpdateOnLaunch={formik.values.scm_update_on_launch}
                  />
                ),
                archive: (
                  <ArchiveSubForm
                    credential={credentials.scm}
                    onCredentialSelection={handleCredentialSelection}
                    scmUpdateOnLaunch={formik.values.scm_update_on_launch}
                  />
                ),
                insights: (
                  <InsightsSubForm
                    credential={credentials.insights}
                    onCredentialSelection={handleCredentialSelection}
                    scmUpdateOnLaunch={formik.values.scm_update_on_launch}
                    autoPopulateCredential={
                      !project?.id || project?.scm_type !== 'insights'
                    }
                  />
                ),
              }[formik.values.scm_type]
            }
          </FormColumnLayout>
        </SubFormLayout>
      )}
    </>
  );
}

function ProjectForm({ project, submitError, ...props }) {
  const { handleCancel, handleSubmit } = props;
  const { summary_fields = {} } = project;
  const { project_base_dir, project_local_paths } = useConfig();
  const [contentError, setContentError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [scmSubFormState, setScmSubFormState] = useState({
    scm_url: '',
    scm_branch: '',
    scm_refspec: '',
    credential: '',
    scm_clean: false,
    scm_delete_on_update: false,
    scm_track_submodules: false,
    scm_update_on_launch: false,
    allow_override: false,
    scm_update_cache_timeout: 0,
  });
  const [scmTypeOptions, setScmTypeOptions] = useState(null);
  const [credentials, setCredentials] = useState({
    scm: { typeId: null, value: null },
    insights: { typeId: null, value: null },
  });

  useEffect(() => {
    async function fetchData() {
      try {
        const credentialResponse = fetchCredentials(summary_fields.credential);
        const {
          data: {
            actions: {
              GET: {
                scm_type: { choices },
              },
            },
          },
        } = await ProjectsAPI.readOptions();

        setCredentials(await credentialResponse);
        setScmTypeOptions(choices);
      } catch (error) {
        setContentError(error);
      } finally {
        setIsLoading(false);
      }
    }

    fetchData();
  }, [summary_fields.credential]);

  if (isLoading) {
    return <ContentLoading />;
  }

  if (contentError) {
    return <ContentError error={contentError} />;
  }

  return (
    <Formik
      initialValues={{
        allow_override: project.allow_override || false,
        base_dir: project_base_dir || '',
        credential: project.credential || '',
        description: project.description || '',
        local_path: project.local_path || '',
        name: project.name || '',
        organization: project.summary_fields?.organization || null,
        scm_branch: project.scm_branch || '',
        scm_clean: project.scm_clean || false,
        scm_delete_on_update: project.scm_delete_on_update || false,
        scm_track_submodules: project.scm_track_submodules || false,
        scm_refspec: project.scm_refspec || '',
        scm_type:
          project.scm_type === ''
            ? 'manual'
            : project.scm_type === undefined
            ? ''
            : project.scm_type,
        scm_update_cache_timeout: project.scm_update_cache_timeout || 0,
        scm_update_on_launch: project.scm_update_on_launch || false,
        scm_url: project.scm_url || '',
        default_environment:
          project.summary_fields?.default_environment || null,
      }}
      onSubmit={handleSubmit}
    >
      {(formik) => (
        <Form autoComplete="off" onSubmit={formik.handleSubmit}>
          <FormColumnLayout>
            <ProjectFormFields
              project={project}
              project_base_dir={project_base_dir}
              project_local_paths={project_local_paths}
              formik={formik}
              setCredentials={setCredentials}
              credentials={credentials}
              scmTypeOptions={scmTypeOptions}
              setScmSubFormState={setScmSubFormState}
              scmSubFormState={scmSubFormState}
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

ProjectForm.propTypes = {
  handleCancel: PropTypes.func.isRequired,
  handleSubmit: PropTypes.func.isRequired,
  project: PropTypes.shape({}),
  submitError: PropTypes.shape({}),
};

ProjectForm.defaultProps = {
  project: {},
  submitError: null,
};

export default ProjectForm;
