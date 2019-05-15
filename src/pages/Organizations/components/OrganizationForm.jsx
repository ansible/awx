import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { withRouter } from 'react-router-dom';
import { Formik, Field } from 'formik';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  Form,
  FormGroup,
} from '@patternfly/react-core';

import { Config } from '../../../contexts/Config';
import { withNetwork } from '../../../contexts/Network';
import FormRow from '../../../components/FormRow';
import FormField from '../../../components/FormField';
import FormActionGroup from '../../../components/FormActionGroup';
import AnsibleSelect from '../../../components/AnsibleSelect';
import InstanceGroupsLookup from './InstanceGroupsLookup';
import { required } from '../../../util/validators';

class OrganizationForm extends Component {
  constructor (props) {
    super(props);

    this.getRelatedInstanceGroups = this.getRelatedInstanceGroups.bind(this);
    this.handleInstanceGroupsChange = this.handleInstanceGroupsChange.bind(this);
    this.handleSubmit = this.handleSubmit.bind(this);

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
      api,
      organization: { id }
    } = this.props;
    const { data } = await api.getOrganizationInstanceGroups(id);
    return data.results;
  }

  isEditingNewOrganization () {
    const { organization } = this.props;
    return !organization.id;
  }

  handleInstanceGroupsChange (instanceGroups) {
    this.setState({ instanceGroups });
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
    const { organization, handleCancel, i18n } = this.props;
    const { instanceGroups, formIsValid, error } = this.state;
    const defaultVenv = '/venv/ansible/';

    return (
      <Formik
        initialValues={{
          name: organization.name,
          description: organization.description,
          custom_virtualenv: organization.custom_virtualenv || '',
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

OrganizationForm.propTypes = {
  organization: PropTypes.shape(),
  handleSubmit: PropTypes.func.isRequired,
  handleCancel: PropTypes.func.isRequired,
};

OrganizationForm.defaultProps = {
  organization: {
    name: '',
    description: '',
    custom_virtualenv: '',
  }
};

OrganizationForm.contextTypes = {
  custom_virtualenvs: PropTypes.arrayOf(PropTypes.string)
};

export { OrganizationForm as _OrganizationForm };
export default withI18n()(withNetwork(withRouter(OrganizationForm)));
