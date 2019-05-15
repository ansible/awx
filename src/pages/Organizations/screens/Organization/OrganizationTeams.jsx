import React, { Fragment } from 'react';
import PropTypes from 'prop-types';
import { withRouter } from 'react-router-dom';
import PaginatedDataList from '../../../../components/PaginatedDataList';
import { getQSConfig, parseNamespacedQueryString } from '../../../../util/qs';
import { withNetwork } from '../../../../contexts/Network';

const QS_CONFIG = getQSConfig('team', {
  page: 1,
  page_size: 5,
  order_by: 'name',
});

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

  async readOrganizationTeamsList () {
    const { id, api, handleHttpError, location } = this.props;
    const params = parseNamespacedQueryString(QS_CONFIG, location.search);
    this.setState({ isLoading: true, error: null });
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
      handleHttpError(error) || this.setState({
        error,
        isLoading: false,
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
          <PaginatedDataList
            items={teams}
            itemCount={itemCount}
            itemName="team"
            qsConfig={QS_CONFIG}
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
