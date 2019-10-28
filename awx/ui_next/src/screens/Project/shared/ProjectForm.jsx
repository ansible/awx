import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { withRouter, Link } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { withFormik, Field } from 'formik';
import { Config } from '@contexts/Config';
import {
  Form as _Form,
  FormGroup,
  Title as _Title,
} from '@patternfly/react-core';
import AnsibleSelect from '@components/AnsibleSelect';
import FormActionGroup from '@components/FormActionGroup/FormActionGroup';
import FormField, { CheckboxField, FieldTooltip } from '@components/FormField';
import FormRow from '@components/FormRow';
import OrganizationLookup from '@components/Lookup/OrganizationLookup';
import CredentialLookup from '@components/Lookup/CredentialLookup';
import { required } from '@util/validators';
import styled from 'styled-components';

const Form = styled(_Form)`
  padding: 0 24px;
`;

const ScmTypeFormRow = styled(FormRow)`
  background-color: #f5f5f5;
  grid-column: 1 / -1;
  margin: 0 -24px;
  padding: 24px;
`;

const OptionsFormGroup = styled.div`
  grid-column: 1/-1;
`;

const Title = styled(_Title)`
  --pf-c-title--m-md--FontWeight: 700;
  grid-column: 1 / -1;
`;

function ProjectForm(props) {
  const { values, handleCancel, handleSubmit, i18n } = props;
  const [organization, setOrganization] = useState(null);
  const [scmCredential, setScmCredential] = useState(null);
  const [insightsCredential, setInsightsCredential] = useState(null);

  const resetScmTypeFields = (value, form) => {
    if (form.initialValues.scm_type === value) {
      return;
    }
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

  const scmTypeOptions = [
    {
      value: '',
      key: '',
      label: i18n._(t`Choose a SCM Type`),
      isDisabled: true,
    },
    { value: 'manual', key: 'manual', label: i18n._(t`Manual`) },
    {
      value: 'git',
      key: 'git',
      label: i18n._(t`Git`),
    },
    {
      value: 'hg',
      key: 'hg',
      label: i18n._(t`Mercurial`),
    },
    {
      value: 'svn',
      key: 'svn',
      label: i18n._(t`Subversion`),
    },
    {
      value: 'insights',
      key: 'insights',
      label: i18n._(t`Red Hat Insights`),
    },
  ];

  const gitScmTooltip = (
    <span>
      {i18n._(t`Example URLs for GIT SCM include:`)}
      <ul css="margin: 10px 0 10px 20px">
        <li>https://github.com/ansible/ansible.git</li>
        <li>git@github.com:ansible/ansible.git</li>
        <li>git://servername.example.com/ansible.git</li>
      </ul>

      {i18n._(t`Note: When using SSH protocol for GitHub or
          Bitbucket, enter an SSH key only, do not enter a username
          (other than git). Additionally, GitHub and Bitbucket do
          not support password authentication when using SSH. GIT
          read only protocol (git://) does not use username or
          password information.`)}
    </span>
  );

  const hgScmTooltip = (
    <span>
      {i18n._(t`Example URLs for Mercurial SCM include:`)}
      <ul style={{ margin: '10px 0 10px 20px' }}>
        <li>https://bitbucket.org/username/project</li>
        <li>ssh://hg@bitbucket.org/username/project</li>
        <li>ssh://server.example.com/path</li>
      </ul>
      {i18n._(t`Note: Mercurial does not support password authentication
    for SSH. Do not put the username and key in the URL. If using
    Bitbucket and SSH, do not supply your Bitbucket username.
    `)}
    </span>
  );

  const svnScmTooltip = (
    <span>
      {i18n._(t`Example URLs for Subversion SCM include:`)}
      <ul style={{ margin: '10px 0 10px 20px' }}>
        <li>https://github.com/ansible/ansible</li>
        <li>svn://servername.example.com/path</li>
        <li>svn+ssh://servername.example.com/path</li>
      </ul>
    </span>
  );

  const scmUrlTooltips = {
    git: gitScmTooltip,
    hg: hgScmTooltip,
    svn: svnScmTooltip,
  };

  const scmBranchLabels = {
    git: i18n._(t`SCM Branch/Tag/Commit`),
    hg: i18n._(t`SCM Branch/Tag/Revision`),
    svn: i18n._(t`Revision #`),
  };

  return (
    <Form autoComplete="off" onSubmit={handleSubmit}>
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
          validate={required(i18n._(t`Select a value for this field`), i18n)}
          render={({ form }) => {
            return (
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
            );
          }}
        />
        <Field
          name="scm_type"
          validate={required(i18n._(t`Select a value for this field`), i18n)}
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
                data={scmTypeOptions}
                onChange={(event, value) => {
                  form.setFieldValue('scm_type', value);
                  resetScmTypeFields(value, form);
                }}
              />
            </FormGroup>
          )}
        />
        {values.scm_type !== '' && (
          <ScmTypeFormRow>
            <Title size="md">{i18n._(t`Type Details`)}</Title>
            {(values.scm_type === 'git' ||
              values.scm_type === 'hg' ||
              values.scm_type === 'svn') && (
              <FormField
                id="project-scm-url"
                isRequired
                label={i18n._(t`SCM URL`)}
                name="scm_url"
                type="text"
                validate={required(null, i18n)}
                tooltipMaxWidth="350px"
                tooltip={scmUrlTooltips[values.scm_type]}
              />
            )}
            {(values.scm_type === 'git' ||
              values.scm_type === 'hg' ||
              values.scm_type === 'svn') && (
              <FormField
                id="project-scm-branch"
                name="scm_branch"
                type="text"
                label={scmBranchLabels[values.scm_type]}
                tooltip={i18n._(t`Branch to checkout. In addition to branches,
                    you can input tags, commit hashes, and arbitrary refs. Some
                    commit hashes and refs may not be availble unless you also
                    provide a custom refspec.`)}
              />
            )}
            {values.scm_type === 'git' && (
              <FormField
                id="project-scm-refspec"
                label={i18n._(t`SCM Refspec`)}
                name="scm_refspec"
                type="text"
                tooltipMaxWidth="400px"
                tooltip={
                  <span>
                    {i18n._(t`A refspec to fetch (passed to the Ansible git
                        module). This parameter allows access to references via
                        the branch field not otherwise available.`)}
                    <br />
                    <br />
                    {i18n._(
                      t`Note: This field assumes the remote name is "origin".`
                    )}
                    <br />
                    <br />
                    {i18n._(t`Examples include:`)}
                    <ul style={{ margin: '10px 0 10px 20px' }}>
                      <li>refs/*:refs/remotes/origin/*</li>
                      <li>
                        refs/pull/62/head:refs/remotes/origin/pull/62/head
                      </li>
                    </ul>
                    {i18n._(t`The first fetches all references. The second
                        fetches the Github pull request number 62, in this example
                        the branch needs to be "pull/62/head".`)}
                    <br />
                    <br />
                    {i18n._(t`For more information, refer to the`)}{' '}
                    <Link to="https://docs.ansible.com/ansible-tower/latest/html/userguide/projects.html#manage-playbooks-using-source-control">
                      {i18n._(t`Ansible Tower Documentation.`)}
                    </Link>
                  </span>
                }
              />
            )}
            {(values.scm_type === 'git' ||
              values.scm_type === 'hg' ||
              values.scm_type === 'svn') && (
              <Field
                name="credential"
                render={({ form }) => (
                  <CredentialLookup
                    credentialTypeId={2}
                    label={i18n._(t`SCM Credential`)}
                    value={scmCredential}
                    onChange={value => {
                      form.setFieldValue('credential', value.id);
                      setScmCredential(value);
                    }}
                  />
                )}
              />
            )}
            {values.scm_type === 'insights' && (
              <Field
                name="credential"
                validate={required(
                  i18n._(t`Select a value for this field`),
                  i18n
                )}
                render={({ form }) => (
                  <CredentialLookup
                    credentialTypeId={14}
                    label={i18n._(t`Insights Credential`)}
                    helperTextInvalid={form.errors.credential}
                    isValid={
                      !form.touched.credential || !form.errors.credential
                    }
                    onBlur={() => form.setFieldTouched('credential')}
                    onChange={value => {
                      form.setFieldValue('credential', value.id);
                      setInsightsCredential(value);
                    }}
                    value={insightsCredential}
                    required
                  />
                )}
              />
            )}
            {/*
                PF Bug: FormGroup doesn't pass down className
                Workaround is to wrap FormGroup with an extra div
                Cleanup when upgraded to @patternfly/react-core@3.103.4
              */}
            {values.scm_type !== 'manual' && (
              <OptionsFormGroup>
                <FormGroup
                  fieldId="project-option-checkboxes"
                  label={i18n._(t`Options`)}
                >
                  <FormRow>
                    <CheckboxField
                      id="option-scm-clean"
                      name="scm_clean"
                      label={i18n._(t`Clean`)}
                      tooltip={i18n._(
                        t`Remove any local modifications prior to performing an update.`
                      )}
                    />
                    <CheckboxField
                      id="option-scm-delete-on-update"
                      name="scm_delete_on_update"
                      label={i18n._(t`Delete`)}
                      tooltip={i18n._(
                        t`Delete the local repository in its entirety prior to
                          performing an update. Depending on the size of the
                          repository this may significantly increase the amount
                          of time required to complete an update.`
                      )}
                    />
                    <CheckboxField
                      id="option-scm-update-on-launch"
                      name="scm_update_on_launch"
                      label={i18n._(t`Update Revision on Launch`)}
                      tooltip={i18n._(
                        t`Each time a job runs using this project, update the
                          revision of the project prior to starting the job.`
                      )}
                    />
                    {values.scm_type !== 'insights' && (
                      <CheckboxField
                        id="option-allow-override"
                        name="allow_override"
                        label={i18n._(t`Allow Branch Override`)}
                        tooltip={i18n._(
                          t`Allow changing the SCM branch or revision in a job
                            template that uses this project.`
                        )}
                      />
                    )}
                  </FormRow>
                </FormGroup>
              </OptionsFormGroup>
            )}
            {values.scm_type !== 'manual' && values.scm_update_on_launch && (
              <>
                <Title size="md">{i18n._(t`Option Details`)}</Title>
                <FormField
                  id="project-cache-timeout"
                  name="scm_update_cache_timeout"
                  type="number"
                  min="0"
                  label={i18n._(t`Cache Timeout`)}
                  tooltip={i18n._(t`Time in seconds to consider a project
                        to be current. During job runs and callbacks the task
                        system will evaluate the timestamp of the latest project
                        update. If it is older than Cache Timeout, it is not
                        considered current, and a new project update will be
                        performed.`)}
                />
              </>
            )}
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
      <FormActionGroup onCancel={handleCancel} onSubmit={handleSubmit} />
    </Form>
  );
}

const FormikApp = withFormik({
  mapPropsToValues(props) {
    const { project = {} } = props;

    return {
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
      scm_update_on_launch: project.scm_update_on_launch || false,
      scm_url: project.scm_url || '',
      scm_update_cache_timeout: project.scm_update_cache_timeout || 0,
      allow_override: project.allow_override || false,
    };
  },
  handleSubmit: (values, { props }) => props.handleSubmit(values),
})(ProjectForm);

ProjectForm.propTypes = {
  handleCancel: PropTypes.func.isRequired,
  handleSubmit: PropTypes.func.isRequired,
  project: PropTypes.shape({}),
};

ProjectForm.defaultProps = {
  project: {},
};

export default withI18n()(withRouter(FormikApp));
