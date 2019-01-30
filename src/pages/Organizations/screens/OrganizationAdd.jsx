import React from 'react';
import PropTypes from 'prop-types';
import { withRouter } from 'react-router-dom';
import {
  PageSection,
  Form,
  FormGroup,
  TextInput,
  ActionGroup,
  Toolbar,
  ToolbarGroup,
  Button,
  Gallery,
  Card,
  CardBody,
} from '@patternfly/react-core';

import { ConfigContext } from '../../../context';
import Lookup from '../../../components/Lookup';
import AnsibleSelect from '../../../components/AnsibleSelect';

const format = (data) => {
  const results = data.results.map((result) => ({
    id: result.id,
    name: result.name,
    isChecked: false
  }));
  return results;
};

class OrganizationAdd extends React.Component {
  constructor (props) {
    super(props);

    this.handleChange = this.handleChange.bind(this);
    this.onSelectChange = this.onSelectChange.bind(this);
    this.onSubmit = this.onSubmit.bind(this);
    this.resetForm = this.resetForm.bind(this);
    this.onSuccess = this.onSuccess.bind(this);
    this.onCancel = this.onCancel.bind(this);
    this.updateSelectedInstanceGroups = this.updateSelectedInstanceGroups.bind(this);
  }

  state = {
    name: '',
    description: '',
    results: [],
    custom_virtualenv: '',
    error: '',
    selectedInstanceGroups: []
  };

  async componentDidMount () {
    const { api } = this.props;
    try {
      const { data } = await api.getInstanceGroups();
      const results = format(data);
      this.setState({ results });
    } catch (error) {
      this.setState({ error });
    }
  }

  onSelectChange (value) {
    this.setState({ custom_virtualenv: value });
  }

  async onSubmit () {
    const { api } = this.props;
    const { name, description, custom_virtualenv } = this.state;
    const data = {
      name,
      description,
      custom_virtualenv
    };
    const { selectedInstanceGroups } = this.state;
    try {
      const { data: response } = await api.createOrganization(data);
      const url = response.related.instance_groups;
      try {
        if (selectedInstanceGroups.length > 0) {
          selectedInstanceGroups.forEach(async (select) => {
            await api.createInstanceGroups(url, select.id);
          });
        }
      } catch (err) {
        this.setState({ error: err });
      } finally {
        this.resetForm();
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

  updateSelectedInstanceGroups (selectedInstanceGroups) {
    this.setState({ selectedInstanceGroups });
  }

  handleChange (_, evt) {
    this.setState({ [evt.target.name]: evt.target.value });
  }

  resetForm () {
    this.setState({
      name: '',
      description: '',
    });
    const { results } = this.state;
    const reset = results.map((result) => ({ id: result.id, name: result.name, isChecked: false }));
    this.setState({ results: reset });
  }

  render () {
    const {
      name,
      results,
      description,
      custom_virtualenv,
      selectedInstanceGroups,
      error
    } = this.state;
    const enabled = name.length > 0; // TODO: add better form validation

    return (
      <PageSection>
        <Card>
          <CardBody>
            <Form autoComplete="off">
              <Gallery gutter="md">
                <FormGroup
                  label="Name"
                  isRequired
                  fieldId="add-org-form-name"
                >
                  <TextInput
                    isRequired
                    type="text"
                    id="add-org-form-name"
                    name="name"
                    value={name}
                    onChange={this.handleChange}
                  />
                </FormGroup>
                <FormGroup label="Description" fieldId="add-org-form-description">
                  <TextInput
                    id="add-org-form-description"
                    name="description"
                    value={description}
                    onChange={this.handleChange}
                  />
                </FormGroup>
                <FormGroup label="Instance Groups" fieldId="simple-form-instance-groups">
                  <Lookup
                    lookupHeader="Instance Groups"
                    onLookupSave={this.updateSelectedInstanceGroups}
                    data={results}
                    selected={selectedInstanceGroups}
                  />
                </FormGroup>
                <ConfigContext.Consumer>
                  {({ custom_virtualenvs }) => (
                    <AnsibleSelect
                      labelName="Ansible Environment"
                      selected={custom_virtualenv}
                      selectChange={this.onSelectChange}
                      data={custom_virtualenvs}
                    />
                  )}
                </ConfigContext.Consumer>
              </Gallery>
              <ActionGroup className="at-align-right">
                <Toolbar>
                  <ToolbarGroup>
                    <Button className="at-C-SubmitButton" variant="primary" onClick={this.onSubmit} isDisabled={!enabled}>Save</Button>
                  </ToolbarGroup>
                  <ToolbarGroup>
                    <Button className="at-C-CancelButton" variant="secondary" onClick={this.onCancel}>Cancel</Button>
                  </ToolbarGroup>
                </Toolbar>
              </ActionGroup>
              { error ? <div>error</div> : '' }
            </Form>
          </CardBody>
        </Card>
      </PageSection>
    );
  }
}

OrganizationAdd.contextTypes = {
  custom_virtualenvs: PropTypes.arrayOf(PropTypes.string)
};

export default withRouter(OrganizationAdd);
