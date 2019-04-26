import React, { Component } from 'react';

import { withNetwork } from '../../../../contexts/Network';

import NotificationsList from '../../../../components/NotificationsList/Notifications.list';

class OrganizationNotifications extends Component {
  constructor (props) {
    super(props);

    this.readOrgNotifications = this.readOrgNotifications.bind(this);
    this.readOrgNotificationSuccess = this.readOrgNotificationSuccess.bind(this);
    this.readOrgNotificationError = this.readOrgNotificationError.bind(this);
    this.createOrgNotificationSuccess = this.createOrgNotificationSuccess.bind(this);
    this.createOrgNotificationError = this.createOrgNotificationError.bind(this);
  }

  readOrgNotifications (id, reqParams) {
    const { api } = this.props;
    return api.getOrganizationNotifications(id, reqParams);
  }

  readOrgNotificationSuccess (id, reqParams) {
    const { api } = this.props;
    return api.getOrganizationNotificationSuccess(id, reqParams);
  }

  readOrgNotificationError (id, reqParams) {
    const { api } = this.props;
    return api.getOrganizationNotificationError(id, reqParams);
  }

  createOrgNotificationSuccess (id, data) {
    const { api } = this.props;
    return api.createOrganizationNotificationSuccess(id, data);
  }

  createOrgNotificationError (id, data) {
    const { api } = this.props;
    return api.createOrganizationNotificationError(id, data);
  }

  render () {
    const {
      canToggleNotifications
    } = this.props;

    return (
      <NotificationsList
        canToggleNotifications={canToggleNotifications}
        onCreateError={this.createOrgNotificationError}
        onCreateSuccess={this.createOrgNotificationSuccess}
        onReadError={this.readOrgNotificationError}
        onReadNotifications={this.readOrgNotifications}
        onReadSuccess={this.readOrgNotificationSuccess}
      />
    );
  }
}

export { OrganizationNotifications as _OrganizationNotifications };
export default withNetwork(OrganizationNotifications);
