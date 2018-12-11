import React, { Fragment } from 'react';
import {
  PageSection,
  PageSectionVariants,
  Title,
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

import { API_ORGANIZATIONS } from '../../../endpoints';
import api from '../../../api';
import AnsibleEnvironmentSelect from '../../../components/AnsibleEnvironmentSelect'
const { light } = PageSectionVariants;

class OrganizationAdd extends React.Component {
  constructor(props) {
    super(props);

    this.handleChange = this.handleChange.bind(this);
    this.onSelectChange = this.onSelectChange.bind(this);
    this.onSubmit = this.onSubmit.bind(this);
    this.resetForm = this.resetForm.bind(this);
  }

  state = {
    name: '',
    description: '',
    instanceGroups: '',
    custom_virtualenv: '',
    post_endpoint: API_ORGANIZATIONS,
  };

  onSelectChange(value, _) {
    this.setState({ custom_virtualenv: value });
  };

  resetForm() {
    this.setState({
      ...this.state,
      name: '',
      description: ''
    })
  }

  handleChange(_, evt) {
    this.setState({ [evt.target.name]: evt.target.value });
  }

  async onSubmit() {
    const data = Object.assign({}, { ...this.state });
    await api.post(API_ORGANIZATIONS, data);
    this.resetForm();
  }

  render() {
    const { name } = this.state;
    const enabled = name.length > 0; // TODO: add better form validation
    return (
      <Fragment>
        <PageSection variant={light} className="pf-m-condensed">
          <Title size="2xl">Organization Add</Title>
        </PageSection>
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
                      value={this.state.name}
                      onChange={this.handleChange}
                    />
                  </FormGroup>
                  <FormGroup label="Description" fieldId="add-org-form-description">
                    <TextInput
                      id="add-org-form-description"
                      name="description"
                      value={this.state.description}
                      onChange={this.handleChange}
                    />
                  </FormGroup>
                  {/* LOOKUP MODAL PLACEHOLDER */}
                  <FormGroup label="Instance Groups" fieldId="simple-form-instance-groups">
                    <TextInput
                      id="add-org-form-instance-groups"
                      name="instance-groups"
                      value={this.state.instanceGroups}
                      onChange={this.handleChange}
                    />
                  </FormGroup>
                  <AnsibleEnvironmentSelect selected={this.state.custom_virtualenv} selectChange={this.onSelectChange} />
                </Gallery>
                <ActionGroup className="at-align-right">
                  <Toolbar>
                    <ToolbarGroup>
                      <Button className="at-C-SubmitButton" variant="primary" onClick={this.onSubmit} isDisabled={!enabled}>Save</Button>
                    </ToolbarGroup>
                    <ToolbarGroup>
                      <Button variant="secondary">Cancel</Button>
                    </ToolbarGroup>
                  </Toolbar>
                </ActionGroup>
              </Form>
            </CardBody>
          </Card>
        </PageSection>
      </Fragment>
    );
  }
}

export default OrganizationAdd;
