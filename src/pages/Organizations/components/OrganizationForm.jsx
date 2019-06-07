import React, { Component, Fragment } from 'react';
import PropTypes from 'prop-types';
import { QuestionCircleIcon } from '@patternfly/react-icons';

import { withRouter } from 'react-router-dom';
import { Formik, Field } from 'formik';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  Tooltip,
  Form,
  FormGroup,
} from '@patternfly/react-core';

import { Config } from '../../../contexts/Config';
import { withNetwork } from '../../../contexts/Network';
import FormRow from '../../../components/FormRow';
import FormField from '../../../components/FormField';
import FormActionGroup from '../../../components/FormActionGroup/FormActionGroup';
import AnsibleSelect from '../../../components/AnsibleSelect';
import InstanceGroupsLookup from './InstanceGroupsLookup';

import { required, minMaxValue } from '../../../util/validators';

class OrganizationForm extends Component {
  constructor (props) {
    super(props);

    this.getRelatedInstanceGroups = this.getRelatedInstanceGroups.bind(this);
    this.handleInstanceGroupsChange = this.handleInstanceGroupsChange.bind(this);
    this.maxHostsChange = this.maxHostsChange.bind(this);
    this.handleSubmit = this.handleSubmit.bind(this);
    this.readUsers = this.readUsers.bind(this);

    this.state = {
      instanceGroups: [],
      initialInstanceGroups: [],
      formIsValid: true,
    };
  }

  async componentDidMount () {
    let instanceGroups = [];

    if (!this.isEditingNewOrganization()) {
      try {
        instanceGroups = await this.getRelatedInstanceGroups();
      } catch (err) {
        this.setState({ error: err });
      }
    }

    this.setState({
      instanceGroups,
      initialInstanceGroups: [...instanceGroups],
    });
  }

  async getRelatedInstanceGroups () {
    const {
      organization: { id }
    } = this.props;
    const { data } = await OrganizationsAPI.readInstanceGroups(id);
    return data.results;
  }

  async readUsers (queryParams) {
    const { api } = this.props;
    console.log(api.readUsers((queryParams, is_superuser)));
    console.log(api.readUsers((queryParams)));
    return true;
   // return api.readUsers((queryParams));
  }

  isEditingNewOrganization () {
    const { organization } = this.props;
    return !organization.id;
  }

  handleInstanceGroupsChange (instanceGroups) {
    this.setState({ instanceGroups });
  }

  maxHostsChange (event) {
    console.log('boop');
  }

  handleSubmit (values) {
    const { handleSubmit } = this.props;
    const { instanceGroups, initialInstanceGroups } = this.state;

    const initialIds = initialInstanceGroups.map(ig => ig.id);
    const updatedIds = instanceGroups.map(ig => ig.id);
    const groupsToAssociate = [...updatedIds]
      .filter(x => !initialIds.includes(x));
    const groupsToDisassociate = [...initialIds]
      .filter(x => !updatedIds.includes(x));

    handleSubmit(values, groupsToAssociate, groupsToDisassociate);
  }

  render () {
    const { organization, handleCancel, i18n, is_superuser } = this.props;
    const { instanceGroups, formIsValid, error } = this.state;
    const defaultVenv = '/venv/ansible/';

    console.log(organization);

    return (
      <Formik
        initialValues={{
          name: organization.name,
          description: organization.description,
          custom_virtualenv: organization.custom_virtualenv || '',
          max_hosts: organization.max_hosts || 0
        }}
        onSubmit={this.handleSubmit}
        render={formik => (
          <Form autoComplete="off" onSubmit={formik.handleSubmit}>
            <FormRow>
              <FormField
                id="org-name"
                name="name"
                type="text"
                label={i18n._(t`Name`)}
                validate={required(null, i18n)}
                isRequired
              />
              <FormField
                id="org-description"
                name="description"
                type="text"
                label={i18n._(t`Description`)}
              />
              <FormField
                id="org-max_hosts"
                name="max_hosts"
                type="number"
                label={<Fragment>
                    {i18n._(t`Max Hosts`)}
                      {' '}
                      {(
                          <Tooltip
                            position="right"
                            content="The maximum number of hosts allowed to be managed by this organization. Value defaults to 0 which means no limit. Refer to the Ansible documentation for more details."
                          >
                            <QuestionCircleIcon />
                          </Tooltip>
                        )
                      }
                    </Fragment>}
                validate={minMaxValue(0, 2147483647, i18n)}
                onChange={(evt) => this.maxHostsChange(evt)}
                // isDisabled={!is_superuser + console.log(is_superuser)}
                // isDisabled={this.readUsers}
                isDisabled={this.readUsers? true: false}
            />
              <Config>
                {({ custom_virtualenvs }) => (
                  custom_virtualenvs && custom_virtualenvs.length > 1 && (
                    <Field
                      name="custom_virtualenv"
                      render={({ field }) => (
                        <FormGroup
                          fieldId="org-custom-virtualenv"
                          label={i18n._(t`Ansible Environment`)}
                        >
                          <AnsibleSelect
                            data={custom_virtualenvs}
                            defaultSelected={defaultVenv}
                            label={i18n._(t`Ansible Environment`)}
                            {...field}
                          />
                        </FormGroup>
                      )}
                    />
                  )
                )}
              </Config>
            </FormRow>
            <InstanceGroupsLookup
              value={instanceGroups}
              onChange={this.handleInstanceGroupsChange}
              tooltip={i18n._(t`Select the Instance Groups for this Organization to run on.`)}
            />
            <FormActionGroup
              onCancel={handleCancel}
              onSubmit={formik.handleSubmit}
              submitDisabled={!formIsValid}
            />
            {error ? <div>error</div> : null}
          </Form>
        )}
      />
    );
  }
}

FormField.propTypes = {
  //consider changing this in FormField.jsx, as many fields may need tooltips in the label
  label: PropTypes.oneOfType ([
    PropTypes.object, 
    PropTypes.string
  ])
}

console.log()

OrganizationForm.propTypes = {
  organization: PropTypes.shape(),
  handleSubmit: PropTypes.func.isRequired,
  handleCancel: PropTypes.func.isRequired,
  };

OrganizationForm.defaultProps = {
  organization: {
    name: '',
    description: '',
    max_hosts: '0',
    custom_virtualenv: '',
  }
};

OrganizationForm.contextTypes = {
  custom_virtualenvs: PropTypes.arrayOf(PropTypes.string)
};

export { OrganizationForm as _OrganizationForm };
export default withI18n()(withNetwork(withRouter(OrganizationForm)));
