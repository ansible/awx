import React, { Component, Fragment } from 'react';
import PropTypes from 'prop-types';
import { QuestionCircleIcon } from '@patternfly/react-icons';

import { withRouter } from 'react-router-dom';
import { Formik, Field } from 'formik';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import { Tooltip, Form, FormGroup } from '@patternfly/react-core';

import { OrganizationsAPI } from '@api';
import { Config } from '@contexts/Config';
import FormRow from '@components/FormRow';
import FormField from '@components/FormField';
import FormActionGroup from '@components/FormActionGroup/FormActionGroup';
import AnsibleSelect from '@components/AnsibleSelect';
import { InstanceGroupsLookup } from '@components/Lookup/';
import { required, minMaxValue } from '@util/validators';

class OrganizationForm extends Component {
  constructor(props) {
    super(props);

    this.getRelatedInstanceGroups = this.getRelatedInstanceGroups.bind(this);
    this.handleInstanceGroupsChange = this.handleInstanceGroupsChange.bind(
      this
    );
    this.handleSubmit = this.handleSubmit.bind(this);

    this.state = {
      instanceGroups: [],
      initialInstanceGroups: [],
      formIsValid: true,
    };
  }

  async componentDidMount() {
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

  async getRelatedInstanceGroups() {
    const {
      organization: { id },
    } = this.props;
    const { data } = await OrganizationsAPI.readInstanceGroups(id);
    return data.results;
  }

  isEditingNewOrganization() {
    const { organization } = this.props;
    return !organization.id;
  }

  handleInstanceGroupsChange(instanceGroups) {
    this.setState({ instanceGroups });
  }

  handleSubmit(values) {
    const { handleSubmit } = this.props;
    const { instanceGroups, initialInstanceGroups } = this.state;

    const initialIds = initialInstanceGroups.map(ig => ig.id);
    const updatedIds = instanceGroups.map(ig => ig.id);
    const groupsToAssociate = [...updatedIds].filter(
      x => !initialIds.includes(x)
    );
    const groupsToDisassociate = [...initialIds].filter(
      x => !updatedIds.includes(x)
    );

    if (
      typeof values.max_hosts !== 'number' ||
      values.max_hosts === 'undefined'
    ) {
      values.max_hosts = 0;
    }

    handleSubmit(values, groupsToAssociate, groupsToDisassociate);
  }

  render() {
    const { organization, handleCancel, i18n, me } = this.props;
    const { instanceGroups, formIsValid, error } = this.state;
    const defaultVenv = {
      label: i18n._(t`Use Default Ansible Environment`),
      value: '/venv/ansible/',
      key: 'default',
    };

    return (
      <Formik
        initialValues={{
          name: organization.name,
          description: organization.description,
          custom_virtualenv: organization.custom_virtualenv || '',
          max_hosts: organization.max_hosts || '0',
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
                label={
                  <Fragment>
                    {i18n._(t`Max Hosts`)}{' '}
                    {
                      <Tooltip
                        position="right"
                        content={i18n._(t`The maximum number of hosts allowed
                          to be managed by this organization. Value defaults to
                          0 which means no limit. Refer to the Ansible
                          documentation for more details.`)}
                      >
                        <QuestionCircleIcon />
                      </Tooltip>
                    }
                  </Fragment>
                }
                validate={minMaxValue(0, 2147483647, i18n)}
                me={me || {}}
                isDisabled={!me.is_superuser}
              />
              <Config>
                {({ custom_virtualenvs }) =>
                  custom_virtualenvs &&
                  custom_virtualenvs.length > 1 && (
                    <Field
                      name="custom_virtualenv"
                      render={({ field }) => (
                        <FormGroup
                          fieldId="org-custom-virtualenv"
                          label={i18n._(t`Ansible Environment`)}
                        >
                          <AnsibleSelect
                            id="org-custom-virtualenv"
                            data={[
                              defaultVenv,
                              ...custom_virtualenvs
                                .filter(datum => datum !== defaultVenv.value)
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
            <InstanceGroupsLookup
              value={instanceGroups}
              onChange={this.handleInstanceGroupsChange}
              tooltip={i18n._(
                t`Select the Instance Groups for this Organization to run on.`
              )}
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
  label: PropTypes.oneOfType([PropTypes.object, PropTypes.string]).isRequired,
};

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
  },
};

OrganizationForm.contextTypes = {
  custom_virtualenvs: PropTypes.arrayOf(PropTypes.string),
};

export { OrganizationForm as _OrganizationForm };
export default withI18n()(withRouter(OrganizationForm));
