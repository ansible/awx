import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { withRouter } from 'react-router-dom';
import { CardBody } from '@patternfly/react-core';

import { OrganizationsAPI } from '@api';
import { Config } from '@contexts/Config';

import OrganizationForm from '../shared/OrganizationForm';

class OrganizationEdit extends Component {
  constructor(props) {
    super(props);

    this.handleSubmit = this.handleSubmit.bind(this);
    this.submitInstanceGroups = this.submitInstanceGroups.bind(this);
    this.handleCancel = this.handleCancel.bind(this);
    this.handleSuccess = this.handleSuccess.bind(this);

    this.state = {
      error: '',
    };
  }

  async handleSubmit(values, groupsToAssociate, groupsToDisassociate) {
    const { organization } = this.props;
    try {
      await OrganizationsAPI.update(organization.id, values);
      await this.submitInstanceGroups(groupsToAssociate, groupsToDisassociate);
      this.handleSuccess();
    } catch (err) {
      this.setState({ error: err });
    }
  }

  handleCancel() {
    const {
      organization: { id },
      history,
    } = this.props;
    history.push(`/organizations/${id}/details`);
  }

  handleSuccess() {
    const {
      organization: { id },
      history,
    } = this.props;
    history.push(`/organizations/${id}/details`);
  }

  async submitInstanceGroups(groupsToAssociate, groupsToDisassociate) {
    const { organization } = this.props;
    try {
      await Promise.all(
        groupsToAssociate.map(id =>
          OrganizationsAPI.associateInstanceGroup(organization.id, id)
        )
      );
      await Promise.all(
        groupsToDisassociate.map(id =>
          OrganizationsAPI.disassociateInstanceGroup(organization.id, id)
        )
      );
    } catch (err) {
      this.setState({ error: err });
    }
  }

  render() {
    const { organization } = this.props;
    const { error } = this.state;

    return (
      <CardBody>
        <Config>
          {({ me }) => (
            <OrganizationForm
              organization={organization}
              handleSubmit={this.handleSubmit}
              handleCancel={this.handleCancel}
              me={me || {}}
            />
          )}
        </Config>
        {error ? <div>error</div> : null}
      </CardBody>
    );
  }
}

OrganizationEdit.propTypes = {
  organization: PropTypes.shape().isRequired,
};

OrganizationEdit.contextTypes = {
  custom_virtualenvs: PropTypes.arrayOf(PropTypes.string),
};

export { OrganizationEdit as _OrganizationEdit };
export default withRouter(OrganizationEdit);
