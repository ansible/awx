import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { withFormik, Field } from 'formik';
import {
  Form,
  FormGroup,
  Tooltip,
  Card,
  Switch,
  Checkbox,
} from '@patternfly/react-core';
import { QuestionCircleIcon as PFQuestionCircleIcon } from '@patternfly/react-icons';
import ContentError from '@components/ContentError';
import ContentLoading from '@components/ContentLoading';
import AnsibleSelect from '@components/AnsibleSelect';
import MultiSelect, { TagMultiSelect } from '@components/MultiSelect';
import FormActionGroup from '@components/FormActionGroup';
import FormField, { CheckboxField } from '@components/FormField';
import FormRow from '@components/FormRow';
import CollapsibleSection from '@components/CollapsibleSection';
import { required } from '@util/validators';
import styled from 'styled-components';
import { JobTemplate } from '@types';
import { InventoriesLookup, InstanceGroupsLookup } from '@components/Lookup';
import ProjectLookup from './ProjectLookup';
import { JobTemplatesAPI, LabelsAPI, ProjectsAPI } from '@api';

const QuestionCircleIcon = styled(PFQuestionCircleIcon)`
  margin-left: 10px;
`;

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
      },
    },
  };

  constructor(props) {
    super(props);
    this.state = {
      hasContentLoading: true,
      contentError: false,
      loadedLabels: [],
      newLabels: [],
      removedLabels: [],
      project: props.template.summary_fields.project,
      inventory: props.template.summary_fields.inventory,
      relatedProjectPlaybooks: props.relatedProjectPlaybooks,
      relatedInstanceGroups: [],
      allowCallbacks: !!props.template.host_config_key,
    };
    this.handleNewLabel = this.handleNewLabel.bind(this);
    this.loadLabels = this.loadLabels.bind(this);
    this.removeLabel = this.removeLabel.bind(this);
    this.handleProjectValidation = this.handleProjectValidation.bind(this);
    this.loadRelatedProjectPlaybooks = this.loadRelatedProjectPlaybooks.bind(
      this
    );
    this.handleInstanceGroupsChange = this.handleInstanceGroupsChange.bind(
      this
    );
  }

  componentDidMount() {
    const { validateField } = this.props;
    validateField('project');
    this.setState({ contentError: null, hasContentLoading: true });
    Promise.all([this.loadLabels(), this.loadRelatedInstanceGroups()]).then(
      () => {
        this.setState({ hasContentLoading: false });
      }
    );
  }

  async loadLabels() {
    // This function assumes that the user has no more than 400
    // labels. For the vast majority of users this will be more thans
    // enough. This can be updated to allow more than 400 labels if we
    // decide it is necessary.
    let loadedLabels;
    try {
      const { data } = await LabelsAPI.read({
        page: 1,
        page_size: 200,
        order_by: 'name',
      });
      loadedLabels = [...data.results];
      if (data.next && data.next.includes('page=2')) {
        const {
          data: { results },
        } = await LabelsAPI.read({
          page: 2,
          page_size: 200,
          order_by: 'name',
        });
        loadedLabels = loadedLabels.concat(results);
      }
      this.setState({ loadedLabels });
    } catch (err) {
      this.setState({ contentError: err });
    }
  }

  async loadRelatedInstanceGroups() {
    const { template } = this.props;
    if (!template.id) {
      return;
    }
    try {
      const { data } = await JobTemplatesAPI.readInstanceGroups(template.id);
      this.setState({
        relatedInstanceGroups: data.results,
      });
    } catch (err) {
      this.setState({ contentError: err });
    }
  }

  handleNewLabel(label) {
    const { newLabels } = this.state;
    const { template, setFieldValue } = this.props;
    const isIncluded = newLabels.some(newLabel => newLabel.name === label.name);
    if (isIncluded) {
      const filteredLabels = newLabels.filter(
        newLabel => newLabel.name !== label
      );
      this.setState({ newLabels: filteredLabels });
    } else if (typeof label === 'string') {
      setFieldValue('newLabels', [
        ...newLabels,
        {
          name: label,
          organization: template.summary_fields.inventory.organization_id,
        },
      ]);
      this.setState({
        newLabels: [
          ...newLabels,
          {
            name: label,
            organization: template.summary_fields.inventory.organization_id,
          },
        ],
      });
    } else {
      setFieldValue('newLabels', [
        ...newLabels,
        { name: label.name, associate: true, id: label.id },
      ]);
      this.setState({
        newLabels: [
          ...newLabels,
          { name: label.name, associate: true, id: label.id },
        ],
      });
    }
  }

  removeLabel(label) {
    const { removedLabels, newLabels } = this.state;
    const { template, setFieldValue } = this.props;

    const isAssociatedLabel = template.summary_fields.labels.results.some(
      tempLabel => tempLabel.id === label.id
    );

    if (isAssociatedLabel) {
      setFieldValue(
        'removedLabels',
        removedLabels.concat({
          disassociate: true,
          id: label.id,
        })
      );
      this.setState({
        removedLabels: removedLabels.concat({
          disassociate: true,
          id: label.id,
        }),
      });
    } else {
      const filteredLabels = newLabels.filter(
        newLabel => newLabel.name !== label.name
      );
      setFieldValue('newLabels', filteredLabels);
      this.setState({ newLabels: filteredLabels });
    }
  }

  async loadRelatedProjectPlaybooks(project) {
    try {
      const { data: playbooks = [] } = await ProjectsAPI.readPlaybooks(project);
      this.setState({ relatedProjectPlaybooks: playbooks });
    } catch (contentError) {
      this.setState({ contentError });
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

  handleInstanceGroupsChange(relatedInstanceGroups) {
    this.setState({ relatedInstanceGroups });
  }

  render() {
    const {
      loadedLabels,
      contentError,
      hasContentLoading,
      inventory,
      project,
      relatedProjectPlaybooks = [],
      newLabels,
      removedLabels,
      relatedInstanceGroups,
      allowCallbacks,
    } = this.state;
    const {
      handleCancel,
      handleSubmit,
      handleBlur,
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
    const playbookOptions = relatedProjectPlaybooks
      .map(playbook => {
        return {
          value: playbook,
          key: playbook,
          label: playbook,
          isDisabled: false,
        };
      })
      .reduce(
        (arr, playbook) => {
          return arr.concat(playbook);
        },
        [
          {
            value: '',
            key: '',
            label: i18n._(t`Choose a playbook`),
            isDisabled: false,
          },
        ]
      );

    const verbosityOptions = [
      { value: '0', key: '0', label: i18n._(t`0 (Normal)`) },
      { value: '1', key: '1', label: i18n._(t`1 (Verbose)`) },
      { value: '2', key: '2', label: i18n._(t`2 (More Verbose)`) },
      { value: '3', key: '3', label: i18n._(t`3 (Debug)`) },
      { value: '4', key: '4', label: i18n._(t`4 (Connection Debug)`) },
    ];

    if (hasContentLoading) {
      return (
        <Card className="awx-c-card">
          <ContentLoading />
        </Card>
      );
    }

    if (contentError) {
      return (
        <Card className="awx-c-card">
          <ContentError error={contentError} />
        </Card>
      );
    }
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
              const isValid =
                form && (!form.touched[field.name] || !form.errors[field.name]);
              return (
                <FormGroup
                  fieldId="template-job-type"
                  helperTextInvalid={form.errors.job_type}
                  isRequired
                  isValid={isValid}
                  label={i18n._(t`Job Type`)}
                >
                  <Tooltip
                    position="right"
                    content={i18n._(t`For job templates, select run to execute
                  the playbook. Select check to only check playbook syntax,
                  test environment setup, and report problems without
                  executing the playbook.`)}
                  >
                    <QuestionCircleIcon />
                  </Tooltip>
                  <AnsibleSelect
                    isValid={isValid}
                    id="job_type"
                    data={jobTypeOptions}
                    {...field}
                  />
                </FormGroup>
              );
            }}
          />
          <Field
            name="inventory"
            validate={required(null, i18n)}
            render={({ form }) => (
              <InventoriesLookup
                value={inventory}
                tooltip={i18n._(t`Select the inventory containing the hosts
                  you want this job to manage.`)}
                onChange={value => {
                  form.setFieldValue('inventory', value.id);
                  this.setState({ inventory: value });
                }}
                required
              />
            )}
          />
          <Field
            name="project"
            validate={this.handleProjectValidation()}
            render={({ form }) => {
              const isValid = form && !form.errors.project;
              return (
                <ProjectLookup
                  helperTextInvalid={form.errors.project}
                  isValid={isValid}
                  value={project}
                  onBlur={handleBlur}
                  tooltip={i18n._(t`Select the project containing the playbook
                  you want this job to execute.`)}
                  onChange={value => {
                    this.loadRelatedProjectPlaybooks(value.id);
                    form.setFieldValue('project', value.id);
                    form.setFieldTouched('project');
                    this.setState({ project: value });
                  }}
                  required
                />
              );
            }}
          />
          <Field
            name="playbook"
            validate={required(i18n._(t`Select a value for this field`), i18n)}
            onBlur={handleBlur}
            render={({ field, form }) => {
              const isValid =
                form && (!form.touched[field.name] || !form.errors[field.name]);
              return (
                <FormGroup
                  fieldId="template-playbook"
                  helperTextInvalid={form.errors.playbook}
                  isRequired
                  isValid={isValid}
                  label={i18n._(t`Playbook`)}
                >
                  <Tooltip
                    position="right"
                    content={i18n._(
                      t`Select the playbook to be executed by this job.`
                    )}
                  >
                    <QuestionCircleIcon />
                  </Tooltip>
                  <AnsibleSelect
                    id="playbook"
                    data={playbookOptions}
                    isValid={isValid}
                    form={form}
                    {...field}
                  />
                </FormGroup>
              );
            }}
          />
        </FormRow>
        <FormRow>
          <FormGroup label={i18n._(t`Labels`)} fieldId="template-labels">
            <Tooltip
              position="right"
              content={i18n._(
                t`Optional labels that describe this job template, such as 'dev' or 'test'. Labels can be used to group and filter job templates and completed jobs.`
              )}
            >
              <QuestionCircleIcon />
            </Tooltip>
            <MultiSelect
              onAddNewItem={this.handleNewLabel}
              onRemoveItem={this.removeLabel}
              associatedItems={template.summary_fields.labels.results}
              options={loadedLabels}
            />
          </FormGroup>
        </FormRow>
        <CollapsibleSection label="Advanced">
          <FormRow>
            <FormField
              id="template-forks"
              name="forks"
              type="number"
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
                  <Tooltip
                    position="right"
                    content={i18n._(t`Control the level of output ansible will
                        produce as the playbook executes.`)}
                  >
                    <QuestionCircleIcon />
                  </Tooltip>
                  <AnsibleSelect data={verbosityOptions} {...field} />
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
                  <Tooltip
                    position="right"
                    content={i18n._(t`If enabled, show the changes made by
                          Ansible tasks, where supported. This is equivalent
                          to Ansible&#x2019s --diff mode.`)}
                  >
                    <QuestionCircleIcon />
                  </Tooltip>
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
          <InstanceGroupsLookup
            value={relatedInstanceGroups}
            onChange={this.handleInstanceGroupsChange}
            tooltip={i18n._(
              t`Select the Instance Groups for this Organization to run on.`
            )}
          />
          <Field
            name="job_tags"
            render={({ field, form }) => (
              <FormGroup
                label={i18n._(t`Job Tags`)}
                fieldId="template-job-tags"
              >
                <Tooltip
                  position="right"
                  content={i18n._(t`Tags are useful when you have a large
                          playbook, and you want to run a specific part of a
                          play or task. Use commas to separate multiple tags.
                          Refer to Ansible Tower documentation for details on
                          the usage of tags.`)}
                >
                  <QuestionCircleIcon />
                </Tooltip>
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
                fieldId="template-skip-tags"
              >
                <Tooltip
                  position="right"
                  content={i18n._(t`Skip tags are useful when you have a
                    large playbook, and you want to skip specific parts of a
                    play or task. Use commas to separate multiple tags. Refer
                    to Ansible Tower documentation for details on the usage
                    of tags.`)}
                >
                  <QuestionCircleIcon />
                </Tooltip>
                <TagMultiSelect
                  value={field.value}
                  onChange={value => form.setFieldValue(field.name, value)}
                />
              </FormGroup>
            )}
          />
          <GridFormGroup isInline label={i18n._(t`Options`)}>
            <CheckboxField
              id="option-privilege-escalation"
              name="become_enabled"
              label={i18n._(t`Privilege Escalation`)}
              tooltip={i18n._(
                t`If enabled, run this playbook as an administrator.`
              )}
            />
            <Checkbox
              aria-label={i18n._(t`Provisioning Callbacks`)}
              label={
                <span>
                  {i18n._(t`Provisioning Callbacks`)}
                  &nbsp;
                  <Tooltip
                    position="right"
                    content={i18n._(
                      t`Enables creation of a provisioning callback URL. Using
                          the URL a host can contact {{BRAND_NAME}} and request a
                          configuration update using this job template.`
                    )}
                  >
                    <QuestionCircleIcon />
                  </Tooltip>
                </span>
              }
              id="option-callbacks"
              checked={allowCallbacks}
              onChange={checked => {
                this.setState({ allowCallbacks: checked });
              }}
            />
            <CheckboxField
              id="option-concurrent"
              name="allow_simultaneous"
              label={i18n._(t`Concurrent Jobs`)}
              tooltip={i18n._(
                t`If enabled, simultaneous runs of this job template will
                    be allowed.`
              )}
            />
            <CheckboxField
              id="option-fact-cache"
              name="use_fact_cache"
              label={i18n._(t`Fact Cache`)}
              tooltip={i18n._(
                t`If enabled, use cached facts if available and store
                    discovered facts in the cache.`
              )}
            />
          </GridFormGroup>
          <FormGroup
            css={`
              ${allowCallbacks ? '' : 'display: none'}
            `}
          >
            HERE
          </FormGroup>
        </CollapsibleSection>
        <FormActionGroup onCancel={handleCancel} onSubmit={handleSubmit} />
      </Form>
    );
  }
}

const FormikApp = withFormik({
  mapPropsToValues(props) {
    const { template = {} } = props;
    const {
      name = '',
      description = '',
      job_type = 'run',
      inventory = '',
      project = '',
      playbook = '',
      forks,
      limit,
      verbosity,
      job_slicing,
      timeout,
      diff_mode,
      job_tags,
      skip_tags,
      become_enabled,
      allow_callbacks,
      allow_simultaneous,
      use_fact_cache,
      summary_fields = { labels: { results: [] } },
    } = { ...template };

    return {
      name: name || '',
      description: description || '',
      job_type: job_type || '',
      inventory: inventory || '',
      project: project || '',
      playbook: playbook || '',
      labels: summary_fields.labels.results,
      forks: forks || '',
      limit: limit || '',
      verbosity: verbosity || '0',
      job_slice_count: job_slicing || '',
      timout: timeout || '',
      diff_mode: diff_mode || false,
      job_tags: job_tags || '',
      skip_tags: skip_tags || '',
      become_enabled: become_enabled || false,
      allow_callbacks: allow_callbacks || false,
      allow_simultaneous: allow_simultaneous || false,
      use_fact_cache: use_fact_cache || false,
    };
  },
  handleSubmit: (values, bag) => bag.props.handleSubmit(values),
})(JobTemplateForm);

export { JobTemplateForm as _JobTemplateForm };
export default withI18n()(withRouter(FormikApp));
