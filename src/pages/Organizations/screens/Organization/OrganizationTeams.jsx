import React from 'react';
import PropTypes from 'prop-types';
import { withRouter } from 'react-router-dom';
import OrganizationTeamsList from '../../components/OrganizationTeamsList';
import { parseQueryString } from '../../../../qs';

const DEFAULT_QUERY_PARAMS = {
  page: 1,
  page_size: 5,
  order_by: 'name',
};

class OrganizationTeams extends React.Component {
  constructor (props) {
    super(props);

    this.readOrganizationTeamsList = this.readOrganizationTeamsList.bind(this);

    this.state = {
      isLoading: false,
      error: null,
      itemCount: 0,
      teams: [],
    };
  }

  componentDidMount () {
    this.readOrganizationTeamsList();
  }

  componentDidUpdate (prevProps) {
    const { location } = this.props;
    if (location !== prevProps.location) {
      this.readOrganizationTeamsList();
    }
  }

  getQueryParams () {
    const { searchString } = this.props;
    const searchParams = parseQueryString(searchString.substring(1));

    return {
      ...DEFAULT_QUERY_PARAMS,
      ...searchParams,
    };
  }

  async readOrganizationTeamsList () {
    const { api, id } = this.props;
    const params = this.getQueryParams();
    this.setState({ isLoading: true });
    try {
      const {
        data: { count = 0, results = [] },
      } = await api.readOrganizationTeamsList(id, params);
      this.setState({
        itemCount: count,
        teams: results,
        isLoading: false,
      });
    } catch (error) {
      this.setState({
        error,
        isLoading: false
      });
    }
  }

  render () {
    const { teams, itemCount, isLoading } = this.state;

    if (isLoading) {
      return <div>Loading...</div>;
    }

    return (
      <OrganizationTeamsList
        teams={teams}
        itemCount={itemCount}
        queryParams={this.getQueryParams()}
      />
    );
  }
}

OrganizationTeams.propTypes = {
  id: PropTypes.number.isRequired,
  searchString: PropTypes.string.isRequired,
  api: PropTypes.shape().isRequired, // TODO: remove?
};

export { OrganizationTeams as _OrganizationTeams };
export default withRouter(OrganizationTeams);
