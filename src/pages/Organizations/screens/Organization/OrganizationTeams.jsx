import React from 'react';
import OrganizationTeamsList from '../../components/OrganizationTeamsList';

class OrganizationTeams extends React.Component {
  constructor (props) {
    super(props);

    this.readOrganizationTeamsList = this.readOrganizationTeamsList.bind(this);
  }

  readOrganizationTeamsList (id, params) {
    const { api } = this.props;
    return api.readOrganizationTeamsList(id, params);
  }

  render () {
    const {
      location,
      match,
      history,
    } = this.props;

    return (
      <OrganizationTeamsList
        onReadTeamsList={this.readOrganizationTeamsList}
        match={match}
        location={location}
        history={history}
      />
    );
  }
}

export default OrganizationTeams;
