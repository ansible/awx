import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { withRouter } from 'react-router-dom';
import { I18n, i18nMark } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  CardBody,
  Form,
  FormGroup,
  TextInput,
} from '@patternfly/react-core';

import { ConfigContext } from '../../../../context';
import FormActionGroup from '../../../../components/FormActionGroup';
import AnsibleSelect from '../../../../components/AnsibleSelect';
import InstanceGroupsLookup from '../../components/InstanceGroupsLookup';

class OrganizationEdit extends Component {
  constructor (props) {
    super(props);

    this.getRelatedInstanceGroups = this.getRelatedInstanceGroups.bind(this);
    this.checkValidity = this.checkValidity.bind(this);
    this.onFieldChange = this.onFieldChange.bind(this);
    this.onLookupSave = this.onLookupSave.bind(this);
    this.onSubmit = this.onSubmit.bind(this);
    this.postInstanceGroups = this.postInstanceGroups.bind(this);
    this.onCancel = this.onCancel.bind(this);
    this.onSuccess = this.onSuccess.bind(this);

    this.state = {
      form: {
        name: {
          value: '',
          isValid: true,
          validation: {
            required: true
          },
          helperTextInvalid: i18nMark('This field must not be blank')
        },
        description: {
          value: ''
        },
        instanceGroups: {
          value: [],
          initialValue: []
        },
        custom_virtualenv: {
          value: '',
          defaultValue: '/venv/ansible/'
        }
      },
      error: '',
      formIsValid: true
    };
  }

  async componentDidMount () {
    const { organization } = this.props;
    const { form: formData } = this.state;

    formData.name.value = organization.name;
    formData.description.value = organization.description;
    formData.custom_virtualenv.value = organization.custom_virtualenv;

    try {
      formData.instanceGroups.value = await this.getRelatedInstanceGroups();
      formData.instanceGroups.initialValue = [...formData.instanceGroups.value];
    } catch (err) {
      this.setState({ error: err });
    }

    this.setState({ form: formData });
  }

  onFieldChange (val, evt) {
    const targetName = evt.target.name;
    const value = val;

    const { form: updatedForm } = this.state;
    const updatedFormEl = { ...updatedForm[targetName] };

    updatedFormEl.value = value;
    updatedForm[targetName] = updatedFormEl;

    updatedFormEl.isValid = (updatedFormEl.validation)
      ? this.checkValidity(updatedFormEl.value, updatedFormEl.validation) : true;

    const formIsValid = (updatedFormEl.validation) ? updatedFormEl.isValid : true;

    this.setState({ form: updatedForm, formIsValid });
  }

  onLookupSave (val, targetName) {
    const { form: updatedForm } = this.state;
    updatedForm[targetName].value = val;

    this.setState({ form: updatedForm });
  }

  async onSubmit () {
    const { api, organization } = this.props;
    const { form: { name, description, custom_virtualenv } } = this.state;
    const formData = { name, description, custom_virtualenv };

    const updatedData = {};
    Object.keys(formData)
      .forEach(formId => {
        updatedData[formId] = formData[formId].value;
      });

    try {
      await api.updateOrganizationDetails(organization.id, updatedData);
      await this.postInstanceGroups();
    } catch (err) {
      this.setState({ error: err });
    } finally {
      this.onSuccess();
    }
  }

  onCancel () {
    const { organization: { id }, history } = this.props;
    history.push(`/organizations/${id}`);
  }

  onSuccess () {
    const { organization: { id }, history } = this.props;
    history.push(`/organizations/${id}`);
  }

  async getRelatedInstanceGroups () {
    const {
      api,
      organization: { id }
    } = this.props;
    const { data } = await api.getOrganizationInstanceGroups(id);
    const { results } = data;
    return results;
  }

  checkValidity = (value, validation) => {
    const isValid = (validation.required)
      ? (value.trim() !== '') : true;

    return isValid;
  }

  async postInstanceGroups () {
    const { api, organization } = this.props;
    const { form: { instanceGroups } } = this.state;
    const url = organization.related.instance_groups;

    const initialInstanceGroups = instanceGroups.initialValue.map(ig => ig.id);
    const updatedInstanceGroups = instanceGroups.value.map(ig => ig.id);

    const groupsToAssociate = [...updatedInstanceGroups]
      .filter(x => !initialInstanceGroups.includes(x));
    const groupsToDisassociate = [...initialInstanceGroups]
      .filter(x => !updatedInstanceGroups.includes(x));

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
    const { api } = this.props;
    const {
      form: {
        name,
        description,
        instanceGroups,
        custom_virtualenv
      },
      formIsValid,
      error
    } = this.state;

    return (
      <CardBody>
        <I18n>
          {({ i18n }) => (
            <Form autoComplete="off">
              <div style={{ display: 'grid', gridGap: '20px', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))' }}>
                <FormGroup
                  fieldId="edit-org-form-name"
                  helperTextInvalid={name.helperTextInvalid}
                  isRequired
                  isValid={name.isValid}
                  label={i18n._(t`Name`)}
                >
                  <TextInput
                    id="edit-org-form-name"
                    isRequired
                    isValid={name.isValid}
                    name="name"
                    onChange={this.onFieldChange}
                    value={name.value || ''}
                  />
                </FormGroup>
                <FormGroup
                  fieldId="edit-org-form-description"
                  label={i18n._(t`Description`)}
                >
                  <TextInput
                    id="edit-org-form-description"
                    name="description"
                    onChange={this.onFieldChange}
                    value={description.value || ''}
                  />
                </FormGroup>
                <ConfigContext.Consumer>
                  {({ custom_virtualenvs }) => (
                    custom_virtualenvs && custom_virtualenvs.length > 1 && (
                      <FormGroup
                        fieldId="edit-org-custom-virtualenv"
                        label={i18n._(t`Ansible Environment`)}
                      >
                        <AnsibleSelect
                          data={custom_virtualenvs}
                          defaultSelected={custom_virtualenv.defaultEnv}
                          label={i18n._(t`Ansible Environment`)}
                          name="custom_virtualenv"
                          onChange={this.onFieldChange}
                          value={custom_virtualenv.value || ''}
                        />
                      </FormGroup>
                    )
                  )}
                </ConfigContext.Consumer>
              </div>
              <InstanceGroupsLookup
                api={api}
                value={instanceGroups.value}
                onChange={this.onLookupSave}
              />
              <FormActionGroup
                onCancel={this.onCancel}
                onSubmit={this.onSubmit}
                submitDisabled={!formIsValid}
              />
              { error ? <div>error</div> : '' }
            </Form>
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
