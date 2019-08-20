import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { withFormik, Field } from 'formik';
import { Form, FormGroup, Tooltip, Card } from '@patternfly/react-core';
import { QuestionCircleIcon as PFQuestionCircleIcon } from '@patternfly/react-icons';
import ContentError from '@components/ContentError';
import ContentLoading from '@components/ContentLoading';
import AnsibleSelect from '@components/AnsibleSelect';
import MultiSelect from '@components/MultiSelect';
import FormActionGroup from '@components/FormActionGroup';
import FormField from '@components/FormField';
import FormRow from '@components/FormRow';
import CollapsibleSection from '@components/CollapsibleSection';
import { required } from '@util/validators';
import styled from 'styled-components';
import { JobTemplate } from '@types';
import InventoriesLookup from './InventoriesLookup';
import ProjectLookup from './ProjectLookup';
import { LabelsAPI, ProjectsAPI } from '@api';

const QuestionCircleIcon = styled(PFQuestionCircleIcon)`
  margin-left: 10px;
`;
const QSConfig = {
  page: 1,
  page_size: 200,
  order_by: 'name',
};

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
    };
    this.handleNewLabel = this.handleNewLabel.bind(this);
    this.loadLabels = this.loadLabels.bind(this);
    this.removeLabel = this.removeLabel.bind(this);
    this.handleProjectValidation = this.handleProjectValidation.bind(this);
    this.loadRelatedProjectPlaybooks = this.loadRelatedProjectPlaybooks.bind(
      this
    );
  }

  async componentDidMount() {
    const { validateField } = this.props;
    await this.loadLabels(QSConfig);
    validateField('project');
  }

  async loadLabels(QueryConfig) {
    // This function assumes that the user has no more than 400
    // labels. For the vast majority of users this will be more thans
    // enough.This can be updated to allow more than 400 labels if we
    // decide it is necessary.
    this.setState({ contentError: null, hasContentLoading: true });
    let loadedLabels;
    try {
      const { data } = await LabelsAPI.read(QueryConfig);
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
    } finally {
      this.setState({ hasContentLoading: false });
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

  render() {
    const {
      loadedLabels,
      contentError,
      hasContentLoading,
      inventory,
      project,
      relatedProjectPlaybooks = [],
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
          Advanced inputs here
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
      playbook = '',
      project = '',
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
    };
  },
  handleSubmit: (values, bag) => bag.props.handleSubmit(values),
})(JobTemplateForm);

export { JobTemplateForm as _JobTemplateForm };
export default withI18n()(withRouter(FormikApp));
