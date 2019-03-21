import React from 'react';
import OrganizationTeamsList from '../../components/OrganizationTeamsList';

class OrganizationTeams extends React.Component {
  constructor (props) {
    super(props);

    this.getOrgTeamsList = this.getOrgTeamsList.bind(this);
  }

  getOrgTeamsList (id, params) {
    const { api } = this.props;
    return api.getOrganizationTeamsList(id, params);
  }

  render () {
    const {
      location,
      match,
      history,
    } = this.props;

    return (
      <OrganizationTeamsList
        getTeamsList={this.getOrgTeamsList}
        match={match}
        location={location}
        history={history}
      />
    );
  }
}

export default OrganizationTeams;
