import React, { Fragment } from 'react';
import PropTypes from 'prop-types';
import { withRouter } from 'react-router-dom';
import { I18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  PageSection,
  Form,
  FormGroup,
  TextInput,
  Gallery,
  Card,
  CardHeader,
  CardBody,
  Button,
  Tooltip,
} from '@patternfly/react-core';
import { QuestionCircleIcon, TimesIcon } from '@patternfly/react-icons';

import { ConfigContext } from '../../../context';
import AnsibleSelect from '../../../components/AnsibleSelect';
import FormActionGroup from '../../../components/FormActionGroup';
import InstanceGroupsLookup from '../components/InstanceGroupsLookup';

class OrganizationAdd extends React.Component {
  constructor (props) {
    super(props);

    this.onFieldChange = this.onFieldChange.bind(this);
    this.onLookupSave = this.onLookupSave.bind(this);
    this.onSubmit = this.onSubmit.bind(this);
    this.onCancel = this.onCancel.bind(this);
    this.onSuccess = this.onSuccess.bind(this);

    this.state = {
      name: '',
      description: '',
      custom_virtualenv: '',
      instanceGroups: [],
      error: '',
      defaultEnv: '/venv/ansible/',
    };
  }

  onFieldChange (val, evt) {
    this.setState({ [evt.target.name]: val || evt.target.value });
  }

  onLookupSave (val, targetName) {
    this.setState({ [targetName]: val });
  }

  async onSubmit () {
    const { api } = this.props;
    const { name, description, custom_virtualenv, instanceGroups } = this.state;
    const data = {
      name,
      description,
      custom_virtualenv
    };
    try {
      const { data: response } = await api.createOrganization(data);
      const instanceGroupsUrl = response.related.instance_groups;
      try {
        if (instanceGroups.length > 0) {
          instanceGroups.forEach(async (select) => {
            await api.associateInstanceGroup(instanceGroupsUrl, select.id);
          });
        }
      } catch (err) {
        this.setState({ error: err });
      } finally {
        this.onSuccess(response.id);
      }
    } catch (err) {
      this.setState({ error: err });
    }
  }

  onCancel () {
    const { history } = this.props;
    history.push('/organizations');
  }

  onSuccess (id) {
    const { history } = this.props;
    history.push(`/organizations/${id}`);
  }

  render () {
    const { api } = this.props;
    const {
      name,
      description,
      custom_virtualenv,
      defaultEnv,
      instanceGroups,
      error
    } = this.state;
    const enabled = name.length > 0; // TODO: add better form validation

    return (
      <PageSection>
        <I18n>
          {({ i18n }) => (
            <Card>
              <CardHeader className="at-u-textRight">
                <Tooltip
                  content={i18n._(t`Close`)}
                  position="top"
                >
                  <Button
                    variant="plain"
                    aria-label={i18n._(t`Close`)}
                    onClick={this.onCancel}
                  >
                    <TimesIcon />
                  </Button>
                </Tooltip>
              </CardHeader>
              <CardBody>
                <Form autoComplete="off">
                  <Gallery gutter="md">
                    <FormGroup
                      label={i18n._(t`Name`)}
                      isRequired
                      fieldId="add-org-form-name"
                    >
                      <TextInput
                        isRequired
                        id="add-org-form-name"
                        name="name"
                        value={name}
                        onChange={this.onFieldChange}
                      />
                    </FormGroup>
                    <FormGroup label={i18n._(t`Description`)} fieldId="add-org-form-description">
                      <TextInput
                        id="add-org-form-description"
                        name="description"
                        value={description}
                        onChange={this.onFieldChange}
                      />
                    </FormGroup>
                    <InstanceGroupsLookup
                      api={api}
                      value={instanceGroups}
                      onChange={this.onLookupSave}
                    />
                    <ConfigContext.Consumer>
                      {({ custom_virtualenvs }) => (
                        custom_virtualenvs && custom_virtualenvs.length > 1 && (
                          <FormGroup
                            label={(
                              <Fragment>
                                {i18n._(t`Ansible Environment`)}
                                {' '}
                                <Tooltip
                                  position="right"
                                  content={i18n._(t`Select the custom Python virtual environment for this organization to run on.`)}
                                >
                                  <QuestionCircleIcon />
                                </Tooltip>
                              </Fragment>
                            )}
                            fieldId="add-org-custom-virtualenv"
                          >
                            <AnsibleSelect
                              label={i18n._(t`Ansible Environment`)}
                              name="custom_virtualenv"
                              value={custom_virtualenv}
                              onChange={this.onFieldChange}
                              data={custom_virtualenvs}
                              defaultSelected={defaultEnv}
                            />
                          </FormGroup>
                        )
                      )}
                    </ConfigContext.Consumer>
                  </Gallery>
                  <FormActionGroup
                    onSubmit={this.onSubmit}
                    submitDisabled={!enabled}
                    onCancel={this.onCancel}
                  />
                  {error ? <div>error</div> : ''}
                </Form>
              </CardBody>
            </Card>
          )}
        </I18n>
      </PageSection>
    );
  }
}

OrganizationAdd.contextTypes = {
  custom_virtualenvs: PropTypes.arrayOf(PropTypes.string)
};

export default withRouter(OrganizationAdd);
