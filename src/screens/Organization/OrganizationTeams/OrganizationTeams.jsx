import React from 'react';
import PropTypes from 'prop-types';
import { withRouter } from 'react-router-dom';
import PaginatedDataList from '../../../components/PaginatedDataList';
import { getQSConfig, parseNamespacedQueryString } from '../../../util/qs';
import { OrganizationsAPI } from '../../../api';

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
      contentError: false,
      contentLoading: true,
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

    this.setState({ contentLoading: true, contentError: false });
    try {
      const {
        data: { count = 0, results = [] },
      } = await OrganizationsAPI.readTeams(id, params);
      this.setState({
        itemCount: count,
        teams: results,
      });
    } catch {
      this.setState({ contentError: true });
    } finally {
      this.setState({ contentLoading: false });
    }
  }

  render () {
    const { contentError, contentLoading, teams, itemCount } = this.state;
    return (
      <PaginatedDataList
        contentError={contentError}
        contentLoading={contentLoading}
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
