import React from 'react';
import AccessList from '../../../../components/AccessList/Access.list';

class OrganizationAccess extends React.Component {
  constructor (props) {
    super(props);

    this.getOrgAccessList = this.getOrgAccessList.bind(this);
    this.getUserRoles = this.getUserRoles.bind(this);
    this.getUserTeams = this.getUserTeams.bind(this);
    this.getTeamRoles = this.getTeamRoles.bind(this);
  }

  getOrgAccessList (id, params) {
    const { api } = this.props;
    return api.getOrganzationAccessList(id, params);
  }

  getUserRoles (id) {
    const { api } = this.props;
    return api.getUserRoles(id);
  }

  getUserTeams (id) {
    const { api } = this.props;
    return api.getUserTeams(id);
  }

  getTeamRoles (id) {
    const { api } = this.props;
    return api.getTeamRoles(id);
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
        getUserTeams={this.getUserTeams}
        getTeamRoles={this.getTeamRoles}
        match={match}
        location={location}
        history={history}
      />
    );
  }
}

export default OrganizationAccess;
