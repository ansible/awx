import React, { Component } from 'react';

import NotificationsList from '../../../../components/NotificationsList/Notifications.list';

class OrganizationNotifications extends Component {
  constructor (props) {
    super(props);

    this.getOrgNotifications = this.getOrgNotifications.bind(this);
    this.getOrgNotificationSuccess = this.getOrgNotificationSuccess.bind(this);
    this.getOrgNotificationError = this.getOrgNotificationError.bind(this);
    this.createOrgNotificationSuccess = this.createOrgNotificationSuccess.bind(this);
    this.createOrgNotificationError = this.createOrgNotificationError.bind(this);
  }

  getOrgNotifications (id, reqParams) {
    const { api } = this.props;
    return api.getOrganizationNotifications(id, reqParams);
  }

  getOrgNotificationSuccess (id, reqParams) {
    const { api } = this.props;
    return api.getOrganizationNotificationSuccess(id, reqParams);
  }

  getOrgNotificationError (id, reqParams) {
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
      location,
      match,
      history
    } = this.props;

    return (
      <NotificationsList
        getNotifications={this.getOrgNotifications}
        getSuccess={this.getOrgNotificationSuccess}
        getError={this.getOrgNotificationError}
        postSuccess={this.createOrgNotificationSuccess}
        postError={this.createOrgNotificationError}
        match={match}
        location={location}
        history={history}
      />
    );
  }
}

export default OrganizationNotifications;
