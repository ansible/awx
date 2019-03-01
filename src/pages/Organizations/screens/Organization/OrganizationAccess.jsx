import React from 'react';
import AccessList from '../../../../components/AccessList';

class OrganizationAccess extends React.Component {
  constructor (props) {
    super(props);

    this.getOrgAccessList = this.getOrgAccessList.bind(this);
    this.getUserRoles = this.getUserRoles.bind(this);
  }

  getOrgAccessList (id, params) {
    const { api } = this.props;
    return api.getOrganzationAccessList(id, params);
  }

  getUserRoles (id) {
    const { api } = this.props;
    return api.getUserRoles(id);
  }

  render () {
    const {
      location,
      match,
      history,
    } = this.props;

    return (
      <AccessList
        getAccessList={this.getOrgAccessList}
        getUserRoles={this.getUserRoles}
        match={match}
        location={location}
        history={history}
      />
    );
  }
}

export default OrganizationAccess;
