/* eslint no-nested-ternary: 0 */
import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Formik, Field } from 'formik';
import { Config } from '@contexts/Config';
import { Form, FormGroup } from '@patternfly/react-core';
import AnsibleSelect from '@components/AnsibleSelect';
import ContentError from '@components/ContentError';
import ContentLoading from '@components/ContentLoading';
import FormActionGroup from '@components/FormActionGroup/FormActionGroup';
import FormField, { FieldTooltip } from '@components/FormField';
import FormRow from '@components/FormRow';
import OrganizationLookup from '@components/Lookup/OrganizationLookup';
import { CredentialTypesAPI, ProjectsAPI } from '@api';
import { required } from '@util/validators';
import styled from 'styled-components';
import {
  GitSubForm,
  HgSubForm,
  SvnSubForm,
  InsightsSubForm,
  SubFormTitle,
} from './ProjectSubForms';

const ScmTypeFormRow = styled(FormRow)`
  background-color: #f5f5f5;
  grid-column: 1 / -1;
  margin: 0 -24px;
  padding: 24px;
`;

const fetchCredentials = async credential => {
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

function ProjectForm({ project, ...props }) {
  const { i18n, handleCancel, handleSubmit } = props;
  const { summary_fields = {} } = project;
  const [contentError, setContentError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [organization, setOrganization] = useState(
    summary_fields.organization || null
  );
  const [scmSubFormState, setScmSubFormState] = useState(null);
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
  }, []);

  const scmFormFields = {
    scm_url: '',
    scm_branch: '',
    scm_refspec: '',
    credential: '',
    scm_clean: false,
    scm_delete_on_update: false,
    scm_update_on_launch: false,
    allow_override: false,
    scm_update_cache_timeout: 0,
  };

  /* Save current scm subform field values to state */
  const saveSubFormState = form => {
    const currentScmFormFields = { ...scmFormFields };

    Object.keys(currentScmFormFields).forEach(label => {
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
      saveSubFormState(form);
    }

    Object.keys(scmFormFields).forEach(label => {
      if (value === form.initialValues.scm_type) {
        form.setFieldValue(label, scmSubFormState[label]);
      } else {
        form.setFieldValue(label, scmFormFields[label]);
      }
      form.setFieldTouched(label, false);
    });
  };

  const handleCredentialSelection = (type, value) => {
    setCredentials({
      ...credentials,
      [type]: {
        ...credentials[type],
        value,
      },
    });
  };

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
        credential: project.credential || '',
        custom_virtualenv: project.custom_virtualenv || '',
        description: project.description || '',
        name: project.name || '',
        organization: project.organization || '',
        scm_branch: project.scm_branch || '',
        scm_clean: project.scm_clean || false,
        scm_delete_on_update: project.scm_delete_on_update || false,
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
      }}
      onSubmit={handleSubmit}
      render={formik => (
        <Form
          autoComplete="off"
          onSubmit={formik.handleSubmit}
          css="padding: 0 24px"
        >
          <FormRow>
            <FormField
              id="project-name"
              label={i18n._(t`Name`)}
              name="name"
              type="text"
              validate={required(null, i18n)}
              isRequired
            />
            <FormField
              id="project-description"
              label={i18n._(t`Description`)}
              name="description"
              type="text"
            />
            <Field
              name="organization"
              validate={required(
                i18n._(t`Select a value for this field`),
                i18n
              )}
              render={({ form }) => (
                <OrganizationLookup
                  helperTextInvalid={form.errors.organization}
                  isValid={
                    !form.touched.organization || !form.errors.organization
                  }
                  onBlur={() => form.setFieldTouched('organization')}
                  onChange={value => {
                    form.setFieldValue('organization', value.id);
                    setOrganization(value);
                  }}
                  value={organization}
                  required
                />
              )}
            />
            <Field
              name="scm_type"
              validate={required(
                i18n._(t`Select a value for this field`),
                i18n
              )}
              render={({ field, form }) => (
                <FormGroup
                  fieldId="project-scm-type"
                  helperTextInvalid={form.errors.scm_type}
                  isRequired
                  isValid={!form.touched.scm_type || !form.errors.scm_type}
                  label={i18n._(t`SCM Type`)}
                >
                  <AnsibleSelect
                    {...field}
                    id="scm_type"
                    data={[
                      {
                        value: '',
                        key: '',
                        label: i18n._(t`Choose an SCM Type`),
                        isDisabled: true,
                      },
                      ...scmTypeOptions.map(([value, label]) => {
                        if (label === 'Manual') {
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
                      form.setFieldValue('scm_type', value);
                      resetScmTypeFields(value, form);
                    }}
                  />
                </FormGroup>
              )}
            />
            {formik.values.scm_type !== '' && (
              <ScmTypeFormRow>
                <SubFormTitle size="md">{i18n._(t`Type Details`)}</SubFormTitle>
                {
                  {
                    git: (
                      <GitSubForm
                        credential={credentials.scm}
                        onCredentialSelection={handleCredentialSelection}
                        scmUpdateOnLaunch={formik.values.scm_update_on_launch}
                      />
                    ),
                    hg: (
                      <HgSubForm
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
                    insights: (
                      <InsightsSubForm
                        credential={credentials.insights}
                        onCredentialSelection={handleCredentialSelection}
                        scmUpdateOnLaunch={formik.values.scm_update_on_launch}
                      />
                    ),
                  }[formik.values.scm_type]
                }
              </ScmTypeFormRow>
            )}
            <Config>
              {({ custom_virtualenvs }) =>
                custom_virtualenvs &&
                custom_virtualenvs.length > 1 && (
                  <Field
                    name="custom_virtualenv"
                    render={({ field }) => (
                      <FormGroup
                        fieldId="project-custom-virtualenv"
                        label={i18n._(t`Ansible Environment`)}
                      >
                        <FieldTooltip
                          content={i18n._(t`Select the playbook to be executed by
                          this job.`)}
                        />
                        <AnsibleSelect
                          id="project-custom-virtualenv"
                          data={[
                            {
                              label: i18n._(t`Use Default Ansible Environment`),
                              value: '/venv/ansible/',
                              key: 'default',
                            },
                            ...custom_virtualenvs
                              .filter(datum => datum !== '/venv/ansible/')
                              .map(datum => ({
                                label: datum,
                                value: datum,
                                key: datum,
                              })),
                          ]}
                          {...field}
                        />
                      </FormGroup>
                    )}
                  />
                )
              }
            </Config>
          </FormRow>
          <FormActionGroup
            onCancel={handleCancel}
            onSubmit={formik.handleSubmit}
          />
        </Form>
      )}
    />
  );
}

ProjectForm.propTypes = {
  handleCancel: PropTypes.func.isRequired,
  handleSubmit: PropTypes.func.isRequired,
  project: PropTypes.shape({}),
};

ProjectForm.defaultProps = {
  project: {},
};

export default withI18n()(ProjectForm);
