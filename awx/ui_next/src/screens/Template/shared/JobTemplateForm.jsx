import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Formik, Field } from 'formik';
import { Form, FormGroup, Tooltip } from '@patternfly/react-core';
import { QuestionCircleIcon as PFQuestionCircleIcon } from '@patternfly/react-icons';
import AnsibleSelect from '@components/AnsibleSelect';
import FormActionGroup from '@components/FormActionGroup';
import FormField from '@components/FormField';
import FormRow from '@components/FormRow';
import { required } from '@util/validators';
import styled from 'styled-components';
import { JobTemplate } from '@types';

const QuestionCircleIcon = styled(PFQuestionCircleIcon)`
  margin-left: 10px;
`;

class JobTemplateForm extends Component {
  static propTypes = {
    template: JobTemplate.isRequired,
    handleCancel: PropTypes.func.isRequired,
    handleSubmit: PropTypes.func.isRequired,
  };

  render() {
    const { handleCancel, handleSubmit, i18n, template } = this.props;

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

    return (
      <Formik
        initialValues={{
          name: template.name,
          description: template.description,
          job_type: template.job_type,
          inventory: template.inventory,
          project: template.project,
          playbook: template.playbook,
        }}
        onSubmit={handleSubmit}
        render={formik => (
          <Form autoComplete="off" onSubmit={formik.handleSubmit}>
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
                render={({ field }) => (
                  <FormGroup
                    fieldId="template-job-type"
                    isRequired
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
                    <AnsibleSelect data={jobTypeOptions} {...field} />
                  </FormGroup>
                )}
              />
              <FormField
                id="template-inventory"
                name="inventory"
                type="number"
                label={i18n._(t`Inventory`)}
                tooltip={i18n._(t`Select the inventory containing the hosts
                you want this job to manage.`)}
                isRequired
                validate={required(null, i18n)}
              />
              <FormField
                id="template-project"
                name="project"
                type="number"
                label={i18n._(t`Project`)}
                tooltip={i18n._(t`Select the project containing the playbook
                you want this job to execute.`)}
                isRequired
                validate={required(null, i18n)}
              />
              <FormField
                id="template-playbook"
                name="playbook"
                type="text"
                label={i18n._(t`Playbook`)}
                tooltip={i18n._(
                  t`Select the playbook to be executed by this job.`
                )}
                isRequired
                validate={required(null, i18n)}
              />
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
}

export default withI18n()(withRouter(JobTemplateForm));
