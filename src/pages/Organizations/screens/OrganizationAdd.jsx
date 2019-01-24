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
import Lookup from '../../../components/Lookup';
import AnsibleSelect from '../../../components/AnsibleSelect';

const { light } = PageSectionVariants;
class OrganizationAdd extends React.Component {
  static format (data) {
    const results = data.results.map((result) => ({
      id: result.id,
      name: result.name,
      isChecked: false
    }));
    return results;
  }

  constructor (props) {
    super(props);

    this.handleChange = this.handleChange.bind(this);
    this.onSelectChange = this.onSelectChange.bind(this);
    this.onLookupChange = this.onLookupChange.bind(this);
    this.onSubmit = this.onSubmit.bind(this);
    this.resetForm = this.resetForm.bind(this);
    this.onSuccess = this.onSuccess.bind(this);
    this.onCancel = this.onCancel.bind(this);
    this.format = this.format.bind(this);
  }

  state = {
    name: '',
    description: '',
    results: [],
    instance_groups: [],
    custom_virtualenv: '',
    error: '',
  };

  async componentDidMount () {
    const { api } = this.props;
    try {
      const { data } = await api.getInstanceGroups();
      const results = this.format(data);
      this.setState({ results });
    } catch (error) {
      this.setState({ getInstanceGroupsError: error });
    }
  }

  onSelectChange (value) {
    this.setState({ custom_virtualenv: value });
  }

  onLookupChange (id) {
    const { results } = this.state;
    const selected = { ...results };
    const index = id - 1;
    selected[index].isChecked = !selected[index].isChecked;
    this.setState({ selected });
  }

  async onSubmit () {
    const { api } = this.props;
    const data = Object.assign({}, { ...this.state });
    const { results } = this.state;
    try {
      const { data: response } = await api.createOrganization(data);
      const url = response.related.instance_groups;
      const selected = results.filter(group => group.isChecked);
      try {
        if (selected.length > 0) {
          selected.forEach(async (select) => {
            await api.createInstanceGroups(url, select.id);
          });
        }
      } catch (err) {
        this.setState({ createInstanceGroupsError: err });
      } finally {
        this.resetForm();
        this.onSuccess(response.id);
      }
    } catch (err) {
      this.setState({ onSubmitError: err });
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
    const { name, results, description, custom_virtualenv } = this.state;
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
                      lookupChange={this.onLookupChange}
                      data={results}
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
              </Form>
            </CardBody>
          </Card>
        </PageSection>
      </Fragment>
    );
  }
}

OrganizationAdd.contextTypes = {
  custom_virtualenvs: PropTypes.arrayOf(PropTypes.string)
};

export default withRouter(OrganizationAdd);
