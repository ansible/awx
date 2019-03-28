import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { withRouter } from 'react-router-dom';
import { CardBody } from '@patternfly/react-core';

import OrganizationForm from '../../components/OrganizationForm';

class OrganizationEdit extends Component {
  constructor (props) {
    super(props);

    // this.getRelatedInstanceGroups = this.getRelatedInstanceGroups.bind(this);
    this.handleSubmit = this.handleSubmit.bind(this);
    this.postInstanceGroups = this.postInstanceGroups.bind(this);
    this.handleCancel = this.handleCancel.bind(this);
    this.handleSuccess = this.handleSuccess.bind(this);

    this.state = {
      error: '',
    };
  }

  async handleSubmit (values, groupsToAssociate, groupsToDisassociate) {
    const { api, organization } = this.props;
    try {
      await api.updateOrganizationDetails(organization.id, values);
      await this.postInstanceGroups(groupsToAssociate, groupsToDisassociate);
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

  async postInstanceGroups (groupsToAssociate, groupsToDisassociate) {
    const { api, organization } = this.props;
    const url = organization.related.instance_groups;

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
    const { error } = this.state;

    return (
      <CardBody>
        <OrganizationForm
          api={api}
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
  api: PropTypes.shape().isRequired,
  organization: PropTypes.shape().isRequired,
};

OrganizationEdit.contextTypes = {
  custom_virtualenvs: PropTypes.arrayOf(PropTypes.string)
};

export { OrganizationEdit as OrganizationEditNoRouter };
export default withRouter(OrganizationEdit);
