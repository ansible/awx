import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { withFormik, Field } from 'formik';
import {
  Form,
  FormGroup,
  Switch,
  Checkbox,
  TextInput,
} from '@patternfly/react-core';
import ContentError from '@components/ContentError';
import ContentLoading from '@components/ContentLoading';
import AnsibleSelect from '@components/AnsibleSelect';
import { TagMultiSelect } from '@components/MultiSelect';
import FormActionGroup from '@components/FormActionGroup';
import FormField, { CheckboxField, FieldTooltip } from '@components/FormField';
import FormRow from '@components/FormRow';
import CollapsibleSection from '@components/CollapsibleSection';
import { required } from '@util/validators';
import styled from 'styled-components';
import { JobTemplate } from '@types';
import {
  InventoryLookup,
  InstanceGroupsLookup,
  ProjectLookup,
  MultiCredentialsLookup,
} from '@components/Lookup';
import { JobTemplatesAPI } from '@api';
import LabelSelect from './LabelSelect';
import PlaybookSelect from './PlaybookSelect';

const GridFormGroup = styled(FormGroup)`
  & > label {
    grid-column: 1 / -1;
  }

  && {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  }
`;

class JobTemplateForm extends Component {
  static propTypes = {
    template: JobTemplate,
    handleCancel: PropTypes.func.isRequired,
    handleSubmit: PropTypes.func.isRequired,
  };

  static defaultProps = {
    template: {
      name: '',
      description: '',
      job_type: 'run',
      inventory: undefined,
      project: undefined,
      playbook: '',
      summary_fields: {
        inventory: null,
        labels: { results: [] },
        project: null,
        credentials: [],
      },
      isNew: true,
    },
  };

  constructor(props) {
    super(props);
    this.state = {
      hasContentLoading: true,
      contentError: false,
      project: props.template.summary_fields.project,
      inventory: props.template.summary_fields.inventory,
      allowCallbacks: !!props.template.host_config_key,
    };
    this.handleProjectValidation = this.handleProjectValidation.bind(this);
    this.loadRelatedInstanceGroups = this.loadRelatedInstanceGroups.bind(this);
  }

  componentDidMount() {
    const { validateField } = this.props;
    this.setState({ contentError: null, hasContentLoading: true });
    // TODO: determine when LabelSelect has finished loading labels
    Promise.all([this.loadRelatedInstanceGroups()]).then(() => {
      this.setState({ hasContentLoading: false });
      validateField('project');
    });
  }

  async loadRelatedInstanceGroups() {
    const { setFieldValue, template } = this.props;
    if (!template.id) {
      return;
    }
    try {
      const { data } = await JobTemplatesAPI.readInstanceGroups(template.id);
      setFieldValue('initialInstanceGroups', data.results);
      setFieldValue('instanceGroups', [...data.results]);
    } catch (err) {
      this.setState({ contentError: err });
    }
  }

  handleProjectValidation() {
    const { i18n, touched } = this.props;
    const { project } = this.state;
    return () => {
      if (!project && touched.project) {
        return i18n._(t`Select a value for this field`);
      }
      if (project && project.status === 'never updated') {
        return i18n._(t`This project needs to be updated`);
      }
      return undefined;
    };
  }

  render() {
    const {
      contentError,
      hasContentLoading,
      inventory,
      project,
      allowCallbacks,
    } = this.state;
    const {
      handleCancel,
      handleSubmit,
      handleBlur,
      setFieldValue,
      i18n,
      template,
    } = this.props;
    const jobTypeOptions = [
      {
        value: '',
        key: '',
        label: i18n._(t`Choose a job type`),
        isDisabled: true,
      },
      { value: 'run', key: 'run', label: i18n._(t`Run`), isDisabled: false },
      {
        value: 'check',
        key: 'check',
        label: i18n._(t`Check`),
        isDisabled: false,
      },
    ];
    const verbosityOptions = [
      { value: '0', key: '0', label: i18n._(t`0 (Normal)`) },
      { value: '1', key: '1', label: i18n._(t`1 (Verbose)`) },
      { value: '2', key: '2', label: i18n._(t`2 (More Verbose)`) },
      { value: '3', key: '3', label: i18n._(t`3 (Debug)`) },
      { value: '4', key: '4', label: i18n._(t`4 (Connection Debug)`) },
    ];
    let callbackUrl;
    if (template && template.related) {
      const { origin } = document.location;
      const path = template.related.callback || `${template.url}callback`;
      callbackUrl = `${origin}${path}`;
    }

    if (hasContentLoading) {
      return <ContentLoading />;
    }

    if (contentError) {
      return <ContentError error={contentError} />;
    }
    const AdvancedFieldsWrapper = template.isNew ? CollapsibleSection : 'div';
    return (
      <Form autoComplete="off" onSubmit={handleSubmit}>
        <FormRow>
          <FormField
            id="template-name"
            name="name"
            type="text"
            label={i18n._(t`Name`)}
            validate={required(null, i18n)}
            isRequired
          />
          <FormField
            id="template-description"
            name="description"
            type="text"
            label={i18n._(t`Description`)}
          />
          <Field
            name="job_type"
            validate={required(null, i18n)}
            onBlur={handleBlur}
            render={({ form, field }) => {
              const isValid = !form.touched.job_type || !form.errors.job_type;
              return (
                <FormGroup
                  fieldId="template-job-type"
                  helperTextInvalid={form.errors.job_type}
                  isRequired
                  isValid={isValid}
                  label={i18n._(t`Job Type`)}
                >
                  <FieldTooltip
                    content={i18n._(t`For job templates, select run to execute
                      the playbook. Select check to only check playbook syntax,
                      test environment setup, and report problems without
                      executing the playbook.`)}
                  />
                  <AnsibleSelect
                    isValid={isValid}
                    id="template-job-type"
                    data={jobTypeOptions}
                    {...field}
                  />
                </FormGroup>
              );
            }}
          />
          <Field
            name="inventory"
            validate={required(i18n._(t`Select a value for this field`), i18n)}
            render={({ form }) => (
              <InventoryLookup
                value={inventory}
                onBlur={() => form.setFieldTouched('inventory')}
                tooltip={i18n._(t`Select the inventory containing the hosts
                  you want this job to manage.`)}
                isValid={!form.touched.inventory || !form.errors.inventory}
                helperTextInvalid={form.errors.inventory}
                onChange={value => {
                  form.setFieldValue('inventory', value.id);
                  form.setFieldValue('organizationId', value.organization);
                  this.setState({ inventory: value });
                }}
                required
                touched={form.touched.inventory}
                error={form.errors.inventory}
              />
            )}
          />
          <Field
            name="project"
            validate={this.handleProjectValidation()}
            render={({ form }) => (
              <ProjectLookup
                value={project}
                onBlur={() => form.setFieldTouched('project')}
                tooltip={i18n._(t`Select the project containing the playbook
                  you want this job to execute.`)}
                isValid={!form.touched.project || !form.errors.project}
                helperTextInvalid={form.errors.project}
                onChange={value => {
                  form.setFieldValue('project', value.id);
                  this.setState({ project: value });
                }}
                required
              />
            )}
          />
          <Field
            name="playbook"
            validate={required(i18n._(t`Select a value for this field`), i18n)}
            onBlur={handleBlur}
            render={({ field, form }) => {
              const isValid = !form.touched.playbook || !form.errors.playbook;
              return (
                <FormGroup
                  fieldId="template-playbook"
                  helperTextInvalid={form.errors.playbook}
                  isRequired
                  isValid={isValid}
                  label={i18n._(t`Playbook`)}
                >
                  <FieldTooltip
                    content={i18n._(
                      t`Select the playbook to be executed by this job.`
                    )}
                  />
                  <PlaybookSelect
                    projectId={form.values.project}
                    isValid={isValid}
                    form={form}
                    field={field}
                    onBlur={() => form.setFieldTouched('playbook')}
                    onError={err => this.setState({ contentError: err })}
                  />
                </FormGroup>
              );
            }}
          />
        </FormRow>
        <FormRow>
          <Field
            name="labels"
            render={({ field }) => (
              <FormGroup label={i18n._(t`Labels`)} fieldId="template-labels">
                <FieldTooltip
                  content={i18n._(t`Optional labels that describe this job template,
                    such as 'dev' or 'test'. Labels can be used to group and filter
                    job templates and completed jobs.`)}
                />
                <LabelSelect
                  value={field.value}
                  onChange={labels => setFieldValue('labels', labels)}
                  onError={err => this.setState({ contentError: err })}
                />
              </FormGroup>
            )}
          />
        </FormRow>
        <FormRow>
          <Field
            name="credentials"
            fieldId="template-credentials"
            render={({ field }) => (
              <MultiCredentialsLookup
                credentials={field.value}
                onChange={newCredentials =>
                  setFieldValue('credentials', newCredentials)
                }
                onError={err => this.setState({ contentError: err })}
                tooltip={i18n._(
                  t`Select credentials that allow Tower to access the nodes this job will be ran against. You can only select one credential of each type. For machine credentials (SSH), checking "Prompt on launch" without selecting credentials will require you to select a machine credential at run time. If you select credentials and check "Prompt on launch", the selected credential(s) become the defaults that can be updated at run time.`
                )}
              />
            )}
          />
        </FormRow>
        <AdvancedFieldsWrapper label="Advanced">
          <FormRow>
            <FormField
              id="template-forks"
              name="forks"
              type="number"
              min="0"
              label={i18n._(t`Forks`)}
              tooltip={
                <span>
                  {i18n._(t`The number of parallel or simultaneous
                  processes to use while executing the playbook. An empty value,
                  or a value less than 1 will use the Ansible default which is
                  usually 5. The default number of forks can be overwritten
                  with a change to`)}{' '}
                  <code>ansible.cfg</code>.{' '}
                  {i18n._(t`Refer to the Ansible documentation for details
                      about the configuration file.`)}
                </span>
              }
            />
            <FormField
              id="template-limit"
              name="limit"
              type="text"
              label={i18n._(t`Limit`)}
              tooltip={i18n._(t`Provide a host pattern to further constrain
                  the list of hosts that will be managed or affected by the
                  playbook. Multiple patterns are allowed. Refer to Ansible
                  documentation for more information and examples on patterns.`)}
            />
            <Field
              name="verbosity"
              render={({ field }) => (
                <FormGroup
                  fieldId="template-verbosity"
                  label={i18n._(t`Verbosity`)}
                >
                  <FieldTooltip
                    content={i18n._(t`Control the level of output ansible will
                      produce as the playbook executes.`)}
                  />
                  <AnsibleSelect
                    id="template-verbosity"
                    data={verbosityOptions}
                    {...field}
                  />
                </FormGroup>
              )}
            />
            <FormField
              id="template-job-slicing"
              name="job_slice_count"
              type="number"
              min="1"
              label={i18n._(t`Job Slicing`)}
              tooltip={i18n._(t`Divide the work done by this job template
                into the specified number of job slices, each running the
                same tasks against a portion of the inventory.`)}
            />
            <FormField
              id="template-timeout"
              name="timeout"
              type="number"
              min="0"
              label={i18n._(t`Timeout`)}
              tooltip={i18n._(t`The amount of time (in seconds) to run
                before the task is canceled. Defaults to 0 for no job
                timeout.`)}
            />
            <Field
              name="diff_mode"
              render={({ field, form }) => (
                <FormGroup
                  fieldId="template-show-changes"
                  label={i18n._(t`Show Changes`)}
                >
                  <FieldTooltip
                    content={i18n._(t`If enabled, show the changes made by
                      Ansible tasks, where supported. This is equivalent
                      to Ansible&#x2019s --diff mode.`)}
                  />
                  <div>
                    <Switch
                      id="template-show-changes"
                      label={field.value ? i18n._(t`On`) : i18n._(t`Off`)}
                      isChecked={field.value}
                      onChange={checked =>
                        form.setFieldValue(field.name, checked)
                      }
                    />
                  </div>
                </FormGroup>
              )}
            />
          </FormRow>
          <Field
            name="instanceGroups"
            render={({ field, form }) => (
              <InstanceGroupsLookup
                css="margin-top: 20px"
                value={field.value}
                onChange={value => form.setFieldValue(field.name, value)}
                tooltip={i18n._(t`Select the Instance Groups for this Organization
                  to run on.`)}
              />
            )}
          />
          <Field
            name="job_tags"
            render={({ field, form }) => (
              <FormGroup
                label={i18n._(t`Job Tags`)}
                css="margin-top: 20px"
                fieldId="template-job-tags"
              >
                <FieldTooltip
                  content={i18n._(t`Tags are useful when you have a large
                    playbook, and you want to run a specific part of a
                    play or task. Use commas to separate multiple tags.
                    Refer to Ansible Tower documentation for details on
                    the usage of tags.`)}
                />
                <TagMultiSelect
                  value={field.value}
                  onChange={value => form.setFieldValue(field.name, value)}
                />
              </FormGroup>
            )}
          />
          <Field
            name="skip_tags"
            render={({ field, form }) => (
              <FormGroup
                label={i18n._(t`Skip Tags`)}
                css="margin-top: 20px"
                fieldId="template-skip-tags"
              >
                <FieldTooltip
                  content={i18n._(t`Skip tags are useful when you have a
                    large playbook, and you want to skip specific parts of a
                    play or task. Use commas to separate multiple tags. Refer
                    to Ansible Tower documentation for details on the usage
                    of tags.`)}
                />
                <TagMultiSelect
                  value={field.value}
                  onChange={value => form.setFieldValue(field.name, value)}
                />
              </FormGroup>
            )}
          />
          <GridFormGroup
            fieldId="template-option-checkboxes"
            isInline
            label={i18n._(t`Options`)}
            css="margin-top: 20px"
          >
            <CheckboxField
              id="option-privilege-escalation"
              name="become_enabled"
              label={i18n._(t`Privilege Escalation`)}
              tooltip={i18n._(t`If enabled, run this playbook as an
                administrator.`)}
            />
            <Checkbox
              aria-label={i18n._(t`Provisioning Callbacks`)}
              label={
                <span>
                  {i18n._(t`Provisioning Callbacks`)}
                  &nbsp;
                  <FieldTooltip
                    content={i18n._(t`Enables creation of a provisioning
                      callback URL. Using the URL a host can contact BRAND_NAME
                      and request a configuration update using this job
                      template.`)}
                  />
                </span>
              }
              id="option-callbacks"
              isChecked={allowCallbacks}
              onChange={checked => {
                this.setState({ allowCallbacks: checked });
              }}
            />
            <CheckboxField
              id="option-concurrent"
              name="allow_simultaneous"
              label={i18n._(t`Concurrent Jobs`)}
              tooltip={i18n._(t`If enabled, simultaneous runs of this job
                template will be allowed.`)}
            />
            <CheckboxField
              id="option-fact-cache"
              name="use_fact_cache"
              label={i18n._(t`Fact Cache`)}
              tooltip={i18n._(t`If enabled, use cached facts if available
                and store discovered facts in the cache.`)}
            />
          </GridFormGroup>
          <div
            css={`
              ${allowCallbacks ? '' : 'display: none'}
              margin-top: 20px;
            `}
          >
            <FormRow>
              {callbackUrl && (
                <FormGroup
                  label={i18n._(t`Provisioning Callback URL`)}
                  fieldId="template-callback-url"
                >
                  <TextInput
                    id="template-callback-url"
                    isDisabled
                    value={callbackUrl}
                  />
                </FormGroup>
              )}
              <FormField
                id="template-host-config-key"
                name="host_config_key"
                label={i18n._(t`Host Config Key`)}
                validate={allowCallbacks ? required(null, i18n) : null}
              />
            </FormRow>
          </div>
        </AdvancedFieldsWrapper>
        <FormActionGroup onCancel={handleCancel} onSubmit={handleSubmit} />
      </Form>
    );
  }
}

const FormikApp = withFormik({
  mapPropsToValues(props) {
    const { template = {} } = props;
    const {
      summary_fields = {
        labels: { results: [] },
        inventory: { organization: null },
      },
    } = template;

    return {
      name: template.name || '',
      description: template.description || '',
      job_type: template.job_type || 'run',
      inventory: template.inventory || '',
      project: template.project || '',
      playbook: template.playbook || '',
      labels: summary_fields.labels.results || [],
      forks: template.forks || 0,
      limit: template.limit || '',
      verbosity: template.verbosity || '0',
      job_slice_count: template.job_slice_count || 1,
      timeout: template.timeout || 0,
      diff_mode: template.diff_mode || false,
      job_tags: template.job_tags || '',
      skip_tags: template.skip_tags || '',
      become_enabled: template.become_enabled || false,
      allow_callbacks: template.allow_callbacks || false,
      allow_simultaneous: template.allow_simultaneous || false,
      use_fact_cache: template.use_fact_cache || false,
      host_config_key: template.host_config_key || '',
      organizationId: summary_fields.inventory.organization_id || null,
      initialInstanceGroups: [],
      instanceGroups: [],
      credentials: summary_fields.credentials || [],
    };
  },
  handleSubmit: (values, { props }) => props.handleSubmit(values),
})(JobTemplateForm);

export { JobTemplateForm as _JobTemplateForm };
export default withI18n()(withRouter(FormikApp));
