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

function ProjectForm(props) {
  const { project, handleCancel, handleSubmit, i18n } = props;
  const [contentError, setContentError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [organization, setOrganization] = useState(null);
  const [scmTypeOptions, setScmTypeOptions] = useState(null);
  const [scmCredential, setScmCredential] = useState({
    typeId: null,
    value: null,
  });
  const [insightsCredential, setInsightsCredential] = useState({
    typeId: null,
    value: null,
  });

  useEffect(() => {
    async function fetchData() {
      try {
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
          {
            data: {
              actions: {
                GET: {
                  scm_type: { choices },
                },
              },
            },
          },
        ] = await Promise.all([
          CredentialTypesAPI.read({ kind: 'scm' }),
          CredentialTypesAPI.read({ name: 'Insights' }),
          ProjectsAPI.readOptions(),
        ]);

        setScmCredential({ typeId: scmCredentialType.id });
        setInsightsCredential({ typeId: insightsCredentialType.id });
        setScmTypeOptions(choices);
      } catch (error) {
        setContentError(error);
      } finally {
        setIsLoading(false);
      }
    }

    fetchData();
  }, []);

  const resetScmTypeFields = form => {
    const scmFormFields = [
      'scm_url',
      'scm_branch',
      'scm_refspec',
      'credential',
      'scm_clean',
      'scm_delete_on_update',
      'scm_update_on_launch',
      'allow_override',
      'scm_update_cache_timeout',
    ];

    scmFormFields.forEach(field => {
      form.setFieldValue(field, form.initialValues[field]);
      form.setFieldTouched(field, false);
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
        scm_type: project.scm_type || '',
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
                      resetScmTypeFields(form);
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
                        setScmCredential={setScmCredential}
                        scmCredential={scmCredential}
                        scmUpdateOnLaunch={formik.values.scm_update_on_launch}
                      />
                    ),
                    hg: (
                      <HgSubForm
                        setScmCredential={setScmCredential}
                        scmCredential={scmCredential}
                        scmUpdateOnLaunch={formik.values.scm_update_on_launch}
                      />
                    ),
                    svn: (
                      <SvnSubForm
                        setScmCredential={setScmCredential}
                        scmCredential={scmCredential}
                        scmUpdateOnLaunch={formik.values.scm_update_on_launch}
                      />
                    ),
                    insights: (
                      <InsightsSubForm
                        setInsightsCredential={setInsightsCredential}
                        insightsCredential={insightsCredential}
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
