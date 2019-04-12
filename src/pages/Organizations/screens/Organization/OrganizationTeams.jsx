import React, { Fragment } from 'react';
import PropTypes from 'prop-types';
import { withRouter } from 'react-router-dom';
import OrganizationTeamsList from '../../components/OrganizationTeamsList';
import { parseQueryString } from '../../../../util/qs';
import { withNetwork } from '../../../../contexts/Network';

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
      isInitialized: false,
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
    const { location } = this.props;
    const searchParams = parseQueryString(location.search.substring(1));

    return {
      ...DEFAULT_QUERY_PARAMS,
      ...searchParams,
    };
  }

  async readOrganizationTeamsList () {
    const { api, handleHttpError, id } = this.props;
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
        isInitialized: true,
      });
    } catch (error) {
      handleHttpError(error) && this.setState({
        error,
        isLoading: false,
        isInitialized: true,
      });
    }
  }

  render () {
    const { teams, itemCount, isLoading, isInitialized, error } = this.state;

    if (error) {
      // TODO: better error state
      return <div>{error.message}</div>;
    }

    // TODO: better loading state
    return (
      <Fragment>
        {isLoading && (<div>Loading...</div>)}
        {isInitialized && (
          <OrganizationTeamsList
            teams={teams}
            itemCount={itemCount}
            queryParams={this.getQueryParams()}
          />
        )}
      </Fragment>
    );
  }
}

OrganizationTeams.propTypes = {
  id: PropTypes.number.isRequired
};

export { OrganizationTeams as _OrganizationTeams };
export default withNetwork(withRouter(OrganizationTeams));
