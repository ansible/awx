import React, { Fragment } from 'react';
import PropTypes from 'prop-types';
import { withRouter } from 'react-router-dom';
import { Trans } from '@lingui/macro';
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

import { ConfigContext } from '../../../context';
import { API_ORGANIZATIONS } from '../../../endpoints';
import api from '../../../api';
import AnsibleSelect from '../../../components/AnsibleSelect'
const { light } = PageSectionVariants;

class OrganizationAdd extends React.Component {
  constructor(props) {
    super(props);

    this.handleChange = this.handleChange.bind(this);
    this.onSelectChange = this.onSelectChange.bind(this);
    this.onSubmit = this.onSubmit.bind(this);
    this.resetForm = this.resetForm.bind(this);
    this.onCancel = this.onCancel.bind(this);
  }

  state = {
    name: '',
    description: '',
    instanceGroups: '',
    custom_virtualenv: '',
    error:'',
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

  onCancel() {
    this.props.history.push('/organizations');
  }

  async componentDidMount() {
    try {
      const { data } = await api.get(API_CONFIG);
      this.setState({ custom_virtualenvs: [...data.custom_virtualenvs] });
      if (this.state.custom_virtualenvs.length > 1) {
        // Show dropdown if we have more than one ansible environment
        this.setState({ hideAnsibleSelect: !this.state.hideAnsibleSelect });
      }
    } catch (error) {
      this.setState({ error })
    }
    
  }
  render() {
    const { name } = this.state;
    const enabled = name.length > 0; // TODO: add better form validation

    return (
      <Fragment>
        <PageSection variant={light} className="pf-m-condensed">
          <Title size="2xl">
            <Trans>Organization Add</Trans>
          </Title>
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
                  <ConfigContext.Consumer>
                    {({ custom_virtualenvs }) =>
                      <AnsibleSelect
                        labelName="Ansible Environment"
                        selected={this.state.custom_virtualenv}
                        selectChange={this.onSelectChange}
                        data={custom_virtualenvs}
                      />
                    }
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
              </Form>
            </CardBody>
          </Card>
        </PageSection>
      </Fragment>
    );
  }
}

OrganizationAdd.contextTypes = {
  custom_virtualenvs: PropTypes.array,
};

export default withRouter(OrganizationAdd);
