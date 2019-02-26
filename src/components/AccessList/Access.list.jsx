import React, { Fragment } from 'react';
import PropTypes from 'prop-types';

import {
  DataList, DataListItem, DataListCell, Text,
  TextContent, TextVariants, Badge
} from '@patternfly/react-core';

import { I18n, i18nMark } from '@lingui/react';
import { t } from '@lingui/macro';

import {
  Link
} from 'react-router-dom';

import BasicChip from '../BasicChip/BasicChip';
import Pagination from '../Pagination/Pagination';
import DataListToolbar from '../DataListToolbar/DataListToolbar';

import {
  parseQueryString,
} from '../../qs';

const userRolesWrapperStyle = {
  display: 'flex',
  flexWrap: 'wrap',
};

const detailWrapperStyle = {
  display: 'grid',
  gridTemplateColumns: 'minmax(70px, max-content) minmax(60px, max-content)',
};

const detailLabelStyle = {
  fontWeight: '700',
  lineHeight: '24px',
  marginRight: '20px',
};

const detailValueStyle = {
  lineHeight: '28px',
  overflow: 'visible',
};

const hiddenStyle = {
  display: 'none',
};

const Detail = ({ label, value, url, isBadge, customStyles }) => {
  let detail = null;
  if (value) {
    detail = (
      <TextContent style={{ ...detailWrapperStyle, ...customStyles }}>
        {url ? (
          <Link to={{ pathname: url }}>
            <Text component={TextVariants.h6} style={detailLabelStyle}>{label}</Text>
          </Link>) : (<Text component={TextVariants.h6} style={detailLabelStyle}>{label}</Text>
        )}
        {isBadge ? (
          <Badge isRead>
            <Text component={TextVariants.p} style={detailValueStyle}>{value}</Text>
          </Badge>
        ) : (
          <Text component={TextVariants.p} style={detailValueStyle}>{value}</Text>
        )}
      </TextContent>
    );
  }
  return detail;
};

class AccessList extends React.Component {
  columns = [
    { name: i18nMark('Username'), key: 'username', isSortable: true },
    { name: i18nMark('First Name'), key: 'first_name', isSortable: true, isNumeric: true },
    { name: i18nMark('Last Name'), key: 'last_name', isSortable: true, isNumeric: true },
  ];

  defaultParams = {
    page: 1,
    page_size: 5,
    order_by: 'username',
  };

  constructor (props) {
    super(props);

    const { page, page_size } = this.getQueryParams();

    this.state = {
      page,
      page_size,
      count: null,
      results: [],
      sortOrder: 'ascending',
      sortedColumnKey: 'username',
      isCompact: true,
    };

    this.fetchOrgAccessList = this.fetchOrgAccessList.bind(this);
    this.onSetPage = this.onSetPage.bind(this);
    this.onExpand = this.onExpand.bind(this);
    this.onCompact = this.onCompact.bind(this);
    this.onSort = this.onSort.bind(this);
    this.getQueryParams = this.getQueryParams.bind(this);
  }

  componentDidMount () {
    const queryParams = this.getQueryParams();

    this.fetchOrgAccessList(queryParams);
  }

  onExpand = () => {
    this.setState({ isCompact: false });
  }

  onCompact = () => {
    this.setState({ isCompact: true });
  }

  onSetPage = (pageNumber, pageSize) => {
    const { sortOrder, sortedColumnKey } = this.state;
    const page = parseInt(pageNumber, 10);
    const page_size = parseInt(pageSize, 10);
    let order_by = sortedColumnKey;

    if (sortOrder === 'descending') {
      order_by = `-${order_by}`;
    }

    const queryParams = this.getQueryParams({ page, page_size, order_by });

    this.fetchOrgAccessList(queryParams);
  };

  getQueryParams (overrides = {}) {
    const { location } = this.props;
    const { search } = location;

    const searchParams = parseQueryString(search.substring(1));

    return Object.assign({}, this.defaultParams, searchParams, overrides);
  }

  onSort = (sortedColumnKey, sortOrder) => {
    const { page_size } = this.state;

    let order_by = sortedColumnKey;

    if (sortOrder === 'descending') {
      order_by = `-${order_by}`;
    }

    const queryParams = this.getQueryParams({ order_by, page_size });

    this.fetchOrgAccessList(queryParams);
  };

  async fetchOrgAccessList (queryParams) {
    const { match, getAccessList, getUserRoles, getTeamRoles, getUserTeams } = this.props;

    const { page, page_size, order_by } = queryParams;

    let sortOrder = 'ascending';
    let sortedColumnKey = order_by;

    if (order_by.startsWith('-')) {
      sortOrder = 'descending';
      sortedColumnKey = order_by.substring(1);
    }

    try {
      const { data:
        { count = null, results = null }
      } = await getAccessList(match.params.id, queryParams);
      const pageCount = Math.ceil(count / page_size);

      const stateToUpdate = {
        count,
        page,
        pageCount,
        page_size,
        sortOrder,
        sortedColumnKey,
        results,
      };

      results.map(async result => {
        result.user_roles = [];
        result.team_roles = [];
        // Grab each Role Type and set as a top-level value
        Object.values(result.summary_fields).filter(value => value.length > 0).forEach(roleType => {
          result.roleType = roleType[0].role.name;
        });

        // Grab User Roles and set as a top-level value
        try {
          const resp = await getUserRoles(result.id);
          const roles = resp.data.results;
          roles.forEach(role => {
            result.user_roles.push(role);
          });
          this.setState(stateToUpdate);
        } catch (error) {
          this.setState({ error });
        }

        // Grab Team Roles and set as a top-level value
        try {
          const team_data = await getUserTeams(result.id);
          const teams = team_data.data.results;
          teams.forEach(async team => {
            let team_roles = await getTeamRoles(team.id);
            team_roles = team_roles.data.results;
            team_roles.forEach(role => {
              result.team_roles.push(role);
            });
            this.setState(stateToUpdate);
          });
        } catch (error) {
          this.setState({ error });
        }
      });
    } catch (error) {
      this.setState({ error });
    }
  }

  render () {
    const {
      results,
      error,
      count,
      page_size,
      pageCount,
      page,
      sortedColumnKey,
      sortOrder,
      isCompact,
    } = this.state;

    if (!results) {
      return null;
    }
    return (
      <I18n>
        {({ i18n }) => (
          <Fragment>
            <DataListToolbar
              sortedColumnKey={sortedColumnKey}
              sortOrder={sortOrder}
              columns={this.columns}
              onSearch={() => {}}
              onSort={this.onSort}
              onCompact={this.onCompact}
              onExpand={this.onExpand}
              isCompact={isCompact}
              showExpandCollapse
            />
            <DataList aria-label={i18n._(t`Access List`)}>
              {results.map(result => (
                <DataListItem aria-labelledby={i18n._(t`access-list-item`)} key={result.id}>
                  <DataListCell>
                    <Detail
                      label={result.username}
                      value={result.roleType}
                      url={result.url}
                      isBadge
                    />
                    {result.first_name || result.last_name ? (
                      <Detail
                        label={i18n._(t`Name`)}
                        value={`${result.first_name} ${result.last_name}`}
                        url={null}
                        customStyles={isCompact ? hiddenStyle : null}
                      />
                    ) : (
                      null
                    )}
                  </DataListCell>
                  <DataListCell>
                    <Detail
                      label=" "
                      value=" "
                      url={null}
                      customStyles={isCompact ? hiddenStyle : null}
                    />
                    {result.user_roles.length > 0 && (
                      <ul style={isCompact
                        ? { ...userRolesWrapperStyle, ...hiddenStyle }
                        : userRolesWrapperStyle}
                      >
                        <Text component={TextVariants.h6} style={detailLabelStyle}>{i18n._(t`User Roles`)}</Text>
                        {result.user_roles.map(role => (
                          <BasicChip
                            key={role.id}
                            text={role.name}
                          />
                        ))}
                      </ul>
                    )}
                    {result.team_roles.length > 0 && (
                      <ul style={isCompact
                        ? { ...userRolesWrapperStyle, ...hiddenStyle }
                        : userRolesWrapperStyle}
                      >
                        <Text component={TextVariants.h6} style={detailLabelStyle}>{i18n._(t`Team Roles`)}</Text>
                        {result.team_roles.map(role => (
                          <BasicChip
                            key={role.id}
                            text={role.name}
                          />
                        ))}
                      </ul>
                    )}
                  </DataListCell>
                </DataListItem>
              ))}
            </DataList>
            <Pagination
              count={count}
              page={page}
              pageCount={pageCount}
              page_size={page_size}
              onSetPage={this.onSetPage}
            />
            { error ? <div>{error}</div> : '' }
          </Fragment>
        )}
      </I18n>
    );
  }
}

AccessList.propTypes = {
  getAccessList: PropTypes.func.isRequired,
  getUserRoles: PropTypes.func.isRequired,
  getUserTeams: PropTypes.func.isRequired,
  getTeamRoles: PropTypes.func.isRequired,
};

export default AccessList;
