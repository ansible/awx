import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { withRouter } from 'react-router-dom';
import { CardBody } from '@patternfly/react-core';
import OrganizationForm from '../../components/OrganizationForm';
import { withNetwork } from '../../../../contexts/Network';

class OrganizationEdit extends Component {
  constructor (props) {
    super(props);

    this.handleSubmit = this.handleSubmit.bind(this);
    this.submitInstanceGroups = this.submitInstanceGroups.bind(this);
    this.handleCancel = this.handleCancel.bind(this);
    this.handleSuccess = this.handleSuccess.bind(this);

    this.state = {
      error: '',
    };
  }

  async handleSubmit (values, groupsToAssociate, groupsToDisassociate) {
    const { api, organization, handleHttpError } = this.props;
    try {
      await api.updateOrganizationDetails(organization.id, values);
      await this.submitInstanceGroups(groupsToAssociate, groupsToDisassociate);
      this.handleSuccess();
    } catch (err) {
      handleHttpError(err) || this.setState({ error: err });
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

  async submitInstanceGroups (groupsToAssociate, groupsToDisassociate) {
    const { api, organization, handleHttpError } = this.props;
    const url = organization.related.instance_groups;

    try {
      await Promise.all(groupsToAssociate.map(id => api.associateInstanceGroup(url, id)));
      await Promise.all(groupsToDisassociate.map(id => api.disassociate(url, id)));
    } catch (err) {
      handleHttpError(err) || this.setState({ error: err });
    }
  }

  render () {
    const { organization } = this.props;
    const { error } = this.state;

    return (
      <CardBody>
        <OrganizationForm
          organization={organization}
          handleSubmit={this.handleSubmit}
          handleCancel={this.handleCancel}
        />
        {error ? <div>error</div> : null}
      </CardBody>
    );
  }
}

OrganizationEdit.propTypes = {
  organization: PropTypes.shape().isRequired,
};

OrganizationEdit.contextTypes = {
  custom_virtualenvs: PropTypes.arrayOf(PropTypes.string)
};

export { OrganizationEdit as _OrganizationEdit };
export default withNetwork(withRouter(OrganizationEdit));
