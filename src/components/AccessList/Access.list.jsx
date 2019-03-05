import React, { Fragment } from 'react';
import PropTypes from 'prop-types';

import {
  DataList, DataListItem, DataListCell, Text,
  TextContent, TextVariants
} from '@patternfly/react-core';

import { I18n, i18nMark } from '@lingui/react';
import { t } from '@lingui/macro';

import {
  Link
} from 'react-router-dom';

import BasicChip from '../BasicChip/BasicChip';
import Pagination from '../Pagination';
import DataListToolbar from '../DataListToolbar';

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

const Detail = ({ label, value, url, customStyles }) => {
  let detail = null;
  if (value) {
    detail = (
      <TextContent style={{ ...detailWrapperStyle, ...customStyles }}>
        {url ? (
          <Link to={{ pathname: url }}>
            <Text component={TextVariants.h6} style={detailLabelStyle}>{label}</Text>
          </Link>) : (<Text component={TextVariants.h6} style={detailLabelStyle}>{label}</Text>
        )}
        <Text component={TextVariants.p} style={detailValueStyle}>{value}</Text>
      </TextContent>
    );
  }
  return detail;
};

const UserName = ({ value, url }) => {
  let username = null;
  if (value) {
    username = (
      <TextContent style={detailWrapperStyle}>
        {url ? (
          <Link to={{ pathname: url }}>
            <Text component={TextVariants.h6} style={detailLabelStyle}>{value}</Text>
          </Link>) : (<Text component={TextVariants.h6} style={detailLabelStyle}>{value}</Text>
        )}
      </TextContent>
    );
  }
  return username;
};

class AccessList extends React.Component {
  columns = [
    { name: i18nMark('Name'), key: 'first_name', isSortable: true },
    { name: i18nMark('Username'), key: 'username', isSortable: true },
    { name: i18nMark('Last Name'), key: 'last_name', isSortable: true },
  ];

  defaultParams = {
    page: 1,
    page_size: 5,
    order_by: 'first_name',
  };

  constructor (props) {
    super(props);

    const { page, page_size } = this.getQueryParams();

    this.state = {
      page,
      page_size,
      count: null,
      sortOrder: 'ascending',
      sortedColumnKey: 'username',
      isCompact: false,
    };

    this.fetchOrgAccessList = this.fetchOrgAccessList.bind(this);
    this.onSetPage = this.onSetPage.bind(this);
    this.onExpand = this.onExpand.bind(this);
    this.onCompact = this.onCompact.bind(this);
    this.onSort = this.onSort.bind(this);
    this.getQueryParams = this.getQueryParams.bind(this);
    this.getTeamRoles = this.getTeamRoles.bind(this);
  }

  componentDidMount () {
    const queryParams = this.getQueryParams();
    try {
      this.fetchOrgAccessList(queryParams);
    } catch (error) {
      this.setState({ error });
    }
  }

  onExpand () {
    this.setState({ isCompact: false });
  }

  onCompact () {
    this.setState({ isCompact: true });
  }

  onSetPage (pageNumber, pageSize) {
    const { sortOrder, sortedColumnKey } = this.state;
    const page = parseInt(pageNumber, 10);
    const page_size = parseInt(pageSize, 10);
    let order_by = sortedColumnKey;

    // Preserve sort order when paginating
    if (sortOrder === 'descending') {
      order_by = `-${order_by}`;
    }

    const queryParams = this.getQueryParams({ page, page_size, order_by });

    this.fetchOrgAccessList(queryParams);
  }

  onSort (sortedColumnKey, sortOrder) {
    const { page_size } = this.state;

    let order_by = sortedColumnKey;

    if (sortOrder === 'descending') {
      order_by = `-${order_by}`;
    }

    const queryParams = this.getQueryParams({ order_by, page_size });

    this.fetchOrgAccessList(queryParams);
  }

  getQueryParams (overrides = {}) {
    const { location } = this.props;
    const { search } = location;

    const searchParams = parseQueryString(search.substring(1));

    return Object.assign({}, this.defaultParams, searchParams, overrides);
  }

  getRoles = roles => Object.values(roles)
    .reduce((val, role) => {
      if (role.length > 0) {
        val.push(role[0].role);
      }
      return val;
    }, []);

  getTeamRoles = roles => roles
    .reduce((val, item) => {
      if (item.role.team_id) {
        const { role } = item;
        val.push(role);
      }
      return val;
    }, []);

  async fetchOrgAccessList (queryParams) {
    const { match, getAccessList } = this.props;

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
      results.forEach((result) => {
        if (result.summary_fields.direct_access) {
          result.teamRoles = this.getTeamRoles(result.summary_fields.direct_access);
        } else {
          result.teamRoles = [];
        }
        result.userRoles = this.getRoles(result.summary_fields) || [];
      });
      this.setState(stateToUpdate);
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
    return (
      <Fragment>
        {!error && !results && (
          <h1>Loading...</h1> // TODO: replace with proper loading state
        )}
        {error && !results && (
          <Fragment>
            <div>{error.message}</div>
            {error.response && (
              <div>{error.response.data.detail}</div>
            )}
          </Fragment> // TODO: replace with proper error handling
        )}
        {results && (
          <Fragment>
            <DataListToolbar
              sortedColumnKey={sortedColumnKey}
              sortOrder={sortOrder}
              columns={this.columns}
              onSearch={() => { }}
              onSort={this.onSort}
              onCompact={this.onCompact}
              onExpand={this.onExpand}
              isCompact={isCompact}
              showExpandCollapse
            />
            <Fragment>
              <I18n>
                {({ i18n }) => (
                  <DataList aria-label={i18n._(t`Access List`)}>
                    {results.map(result => (
                      <DataListItem aria-labelledby={i18n._(t`access-list-item`)} key={result.id}>
                        <DataListCell>
                          <UserName
                            value={result.username}
                            url={result.url}
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
                          {result.userRoles.length > 0 && (
                            <ul style={isCompact
                              ? { ...userRolesWrapperStyle, ...hiddenStyle }
                              : userRolesWrapperStyle}
                            >
                              <Text component={TextVariants.h6} style={detailLabelStyle}>{i18n._(t`User Roles`)}</Text>
                              {result.userRoles.map(role => (
                                <BasicChip
                                  key={role.id}
                                  text={role.name}
                                />
                              ))}
                            </ul>
                          )}
                          {result.teamRoles.length > 0 && (
                            <ul style={isCompact
                              ? { ...userRolesWrapperStyle, ...hiddenStyle }
                              : userRolesWrapperStyle}
                            >
                              <Text component={TextVariants.h6} style={detailLabelStyle}>{i18n._(t`Team Roles`)}</Text>
                              {result.teamRoles.map(role => (
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
                )}
              </I18n>
            </Fragment>
            <Pagination
              count={count}
              page={page}
              pageCount={pageCount}
              page_size={page_size}
              onSetPage={this.onSetPage}
            />
          </Fragment>
        )}
      </Fragment>
    );
  }
}

AccessList.propTypes = {
  getAccessList: PropTypes.func.isRequired,
};

export default AccessList;
