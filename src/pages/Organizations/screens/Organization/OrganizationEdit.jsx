import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { withRouter } from 'react-router-dom';
import { Formik, Field } from 'formik';
import { I18n, i18nMark } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  CardBody,
  Form,
  FormGroup,
} from '@patternfly/react-core';

import { ConfigContext } from '../../../../context';
import FormField from '../../../../components/FormField';
import FormActionGroup from '../../../../components/FormActionGroup';
import AnsibleSelect from '../../../../components/AnsibleSelect';
import InstanceGroupsLookup from '../../components/InstanceGroupsLookup';

function required (message) {
  return value => {
    if (!value.trim()) {
      return message || i18nMark('This field must not be blank');
    }
    return undefined;
  };
}

class OrganizationEdit extends Component {
  constructor (props) {
    super(props);

    this.getRelatedInstanceGroups = this.getRelatedInstanceGroups.bind(this);
    this.handleInstanceGroupsChange = this.handleInstanceGroupsChange.bind(this);
    this.handleSubmit = this.handleSubmit.bind(this);
    this.postInstanceGroups = this.postInstanceGroups.bind(this);
    this.handleCancel = this.handleCancel.bind(this);
    this.handleSuccess = this.handleSuccess.bind(this);

    this.state = {
      initialInstanceGroups: [],
      instanceGroups: [],
      error: '',
      formIsValid: true,
    };
  }

  async componentDidMount () {
    let instanceGroups;
    try {
      instanceGroups = await this.getRelatedInstanceGroups();
    } catch (err) {
      this.setState({ error: err });
    }

    this.setState({
      instanceGroups,
      initialInstanceGroups: instanceGroups,
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

  handleInstanceGroupsChange (instanceGroups) {
    this.setState({ instanceGroups });
  }

  async handleSubmit (values) {
    const { api, organization } = this.props;
    const { instanceGroups } = this.state;
    try {
      await api.updateOrganizationDetails(organization.id, values);
      await this.postInstanceGroups(instanceGroups);
    } catch (err) {
      this.setState({ error: err });
    } finally {
      this.handleSuccess();
    }
  }

  handleCancel () {
    const { organization: { id }, history } = this.props;
    history.push(`/organizations/${id}`);
  }

  handleSuccess () {
    const { organization: { id }, history } = this.props;
    history.push(`/organizations/${id}`);
  }

  async postInstanceGroups (instanceGroups) {
    const { api, organization } = this.props;
    const { initialInstanceGroups } = this.state;
    const url = organization.related.instance_groups;

    const initialIds = initialInstanceGroups.map(ig => ig.id);
    const updatedIds = instanceGroups.map(ig => ig.id);

    const groupsToAssociate = [...updatedIds]
      .filter(x => !initialIds.includes(x));
    const groupsToDisassociate = [...initialIds]
      .filter(x => !updatedIds.includes(x));

    try {
      await Promise.all(groupsToAssociate.map(async id => {
        await api.associateInstanceGroup(url, id);
      }));
      await Promise.all(groupsToDisassociate.map(async id => {
        await api.disassociate(url, id);
      }));
    } catch (err) {
      this.setState({ error: err });
    }
  }

  render () {
    const { api, organization } = this.props;
    const {
      instanceGroups,
      formIsValid,
      error,
    } = this.state;
    const defaultVenv = '/venv/ansible/';

    return (
      <CardBody>
        <I18n>
          {({ i18n }) => (
            <Formik
              initialValues={{
                name: organization.name,
                description: organization.description,
                custom_virtualenv: organization.custom_virtualenv || '',
              }}
              onSubmit={this.handleSubmit}
              render={formik => (
                <Form autoComplete="off" onSubmit={formik.handleSubmit}>
                  <div
                    style={{
                      display: 'grid',
                      gridGap: '20px',
                      gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))'
                    }}
                  >
                    <FormField
                      id="edit-org-form-name"
                      name="name"
                      type="text"
                      label={i18n._(t`Name`)}
                      validate={required()}
                      isRequired
                    />
                    <FormField
                      id="edit-org-form-description"
                      name="description"
                      type="text"
                      label={i18n._(t`Description`)}
                    />
                    <ConfigContext.Consumer>
                      {({ custom_virtualenvs }) => (
                        custom_virtualenvs && custom_virtualenvs.length > 1 && (
                          <Field
                            name="custom_virtualenv"
                            render={({ field }) => (
                              <FormGroup
                                fieldId="edit-org-custom-virtualenv"
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
                    </ConfigContext.Consumer>
                  </div>
                  <InstanceGroupsLookup
                    api={api}
                    value={instanceGroups}
                    onChange={this.handleInstanceGroupsChange}
                  />
                  <FormActionGroup
                    onCancel={this.handleCancel}
                    onSubmit={formik.handleSubmit}
                    submitDisabled={!formIsValid}
                  />
                  { error ? <div>error</div> : '' }
                </Form>
              )}
            />
          )}
        </I18n>
      </CardBody>
    );
  }
}

OrganizationEdit.contextTypes = {
  custom_virtualenvs: PropTypes.arrayOf(PropTypes.string)
};

export default withRouter(OrganizationEdit);
