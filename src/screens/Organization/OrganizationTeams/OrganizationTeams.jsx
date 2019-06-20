import React from 'react';
import PropTypes from 'prop-types';
import { withRouter } from 'react-router-dom';

import { OrganizationsAPI } from '@api';
import PaginatedDataList from '@components/PaginatedDataList';
import { getQSConfig, parseNamespacedQueryString } from '@util/qs';

const QS_CONFIG = getQSConfig('team', {
  page: 1,
  page_size: 5,
  order_by: 'name',
});

class OrganizationTeams extends React.Component {
  constructor (props) {
    super(props);

    this.loadOrganizationTeamsList = this.loadOrganizationTeamsList.bind(this);

    this.state = {
      hasContentError: false,
      hasContentLoading: true,
      itemCount: 0,
      teams: [],
    };
  }

  componentDidMount () {
    this.loadOrganizationTeamsList();
  }

  componentDidUpdate (prevProps) {
    const { location } = this.props;
    if (location !== prevProps.location) {
      this.loadOrganizationTeamsList();
    }
  }

  async loadOrganizationTeamsList () {
    const { id, location } = this.props;
    const params = parseNamespacedQueryString(QS_CONFIG, location.search);

    this.setState({ hasContentLoading: true, hasContentError: false });
    try {
      const {
        data: { count = 0, results = [] },
      } = await OrganizationsAPI.readTeams(id, params);
      this.setState({
        itemCount: count,
        teams: results,
      });
    } catch {
      this.setState({ hasContentError: true });
    } finally {
      this.setState({ hasContentLoading: false });
    }
  }

  render () {
    const { hasContentError, hasContentLoading, teams, itemCount } = this.state;
    return (
      <PaginatedDataList
        hasContentError={hasContentError}
        hasContentLoading={hasContentLoading}
        items={teams}
        itemCount={itemCount}
        itemName="team"
        qsConfig={QS_CONFIG}
      />
    );
  }
}

OrganizationTeams.propTypes = {
  id: PropTypes.number.isRequired
};

export { OrganizationTeams as _OrganizationTeams };
export default withRouter(OrganizationTeams);
