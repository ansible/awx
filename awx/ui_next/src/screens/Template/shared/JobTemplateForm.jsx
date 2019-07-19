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
import InventoriesLookup from './InventoriesLookup';

const QuestionCircleIcon = styled(PFQuestionCircleIcon)`
  margin-left: 10px;
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
      inventory: '',
      job_type: 'run',
      project: '',
      playbook: '',
      summary_fields: {},
    },
  };

  constructor(props) {
    super(props);

    this.state = {
      inventory: props.template.summary_fields.inventory,
    };
  }

  render() {
    const { handleCancel, handleSubmit, i18n, template } = this.props;
    const { inventory } = this.state;

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
                  />
                )}
              />
              {/* <FormGroup
                    fieldId="template-inventory"
                    helperTextInvalid={form.errors.inventory}
                    isRequired
                    label={i18n._(t`Inventory`)}
                  >
                    <Lookup
                      id="template-inventory"
                      lookupHeader={i18n._(t`Inventory`)}
                      name="inventory"
                      value={[field.value]}
                      onLookupSave={(value) => {console.log(value)}}
                      getItems={() => ({
                        data: {
                          results: [{id: 1, name: 'foo'}, {id: 2, name: 'bar'}],
                          count: 2
                        }
                      })}
                      columns={[
                        { name: i18n._(t`Name`), key: 'name', isSortable: true},
                      ]}
                      sortedColumnsKey="name"
                    />
                  </FormGroup> */}
              {/* <FormField
                id="template-inventory"
                name="inventory"
                type="number"
                label={i18n._(t`Inventory`)}
                tooltip={i18n._(t`Select the inventory containing the hosts
                you want this job to manage.`)}
                isRequired
                validate={required(null, i18n)}
              /> */}
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
