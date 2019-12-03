import React from 'react';
import PropTypes from 'prop-types';
import { withRouter } from 'react-router-dom';

import { OrganizationsAPI } from '@api';
import PaginatedDataList from '@components/PaginatedDataList';
import { getQSConfig, parseQueryString } from '@util/qs';

const QS_CONFIG = getQSConfig('team', {
  page: 1,
  page_size: 5,
  order_by: 'name',
});

class OrganizationTeams extends React.Component {
  constructor(props) {
    super(props);

    this.loadOrganizationTeamsList = this.loadOrganizationTeamsList.bind(this);

    this.state = {
      contentError: null,
      hasContentLoading: true,
      itemCount: 0,
      teams: [],
    };
  }

  componentDidMount() {
    this.loadOrganizationTeamsList();
  }

  componentDidUpdate(prevProps) {
    const { location } = this.props;
    if (location !== prevProps.location) {
      this.loadOrganizationTeamsList();
    }
  }

  async loadOrganizationTeamsList() {
    const { id, location } = this.props;
    const params = parseQueryString(QS_CONFIG, location.search);

    this.setState({ hasContentLoading: true, contentError: null });
    try {
      const {
        data: { count = 0, results = [] },
      } = await OrganizationsAPI.readTeams(id, params);
      this.setState({
        itemCount: count,
        teams: results,
      });
    } catch (err) {
      this.setState({ contentError: err });
    } finally {
      this.setState({ hasContentLoading: false });
    }
  }

  render() {
    const { contentError, hasContentLoading, teams, itemCount } = this.state;
    return (
      <PaginatedDataList
        contentError={contentError}
        hasContentLoading={hasContentLoading}
        items={teams}
        itemCount={itemCount}
        pluralizedItemName="Teams"
        qsConfig={QS_CONFIG}
      />
    );
  }
}

OrganizationTeams.propTypes = {
  id: PropTypes.number.isRequired,
};

export { OrganizationTeams as _OrganizationTeams };
export default withRouter(OrganizationTeams);
