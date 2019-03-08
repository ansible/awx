import React, { Fragment } from 'react';
import PropTypes from 'prop-types';

import {
  DataList, DataListItem, DataListCell, Text,
  TextContent, TextVariants, Chip, Alert, AlertActionCloseButton, Button
} from '@patternfly/react-core';

import { I18n, i18nMark } from '@lingui/react';
import { t } from '@lingui/macro';

import {
  Link
} from 'react-router-dom';

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

const buttonGroupStyle = {
  float: 'right',
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
      showWarning: false,
    };

    this.fetchOrgAccessList = this.fetchOrgAccessList.bind(this);
    this.onSetPage = this.onSetPage.bind(this);
    this.onExpand = this.onExpand.bind(this);
    this.onCompact = this.onCompact.bind(this);
    this.onSort = this.onSort.bind(this);
    this.getQueryParams = this.getQueryParams.bind(this);
    this.removeRole = this.removeRole.bind(this);
    this.handleWarning = this.handleWarning.bind(this);
    this.hideWarning = this.hideWarning.bind(this);
    this.confirmDelete = this.confirmDelete.bind(this);
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
        // Separate out roles into user roles or team roles
        // based on whether or not a team_id attribute is present
        const teamRoles = [];
        const userRoles = [];
        Object.values(result.summary_fields).forEach(field => {
          if (field.length > 0) {
            field.forEach(item => {
              const { role } = item;
              if (role.team_id) {
                teamRoles.push(role);
              } else {
                userRoles.push(role);
              }
            });
          }
        });

        result.teamRoles = teamRoles || [];
        result.userRoles = userRoles || [];
      });
      this.setState(stateToUpdate);
    } catch (error) {
      this.setState({ error });
    }
  }

  async removeRole (roleId, resourceId, type) {
    const { removeRole } = this.props;
    const url = `/api/v2/${type}/${resourceId}/roles/`;
    await removeRole(url, roleId);
    const queryParams = this.getQueryParams();
    try {
      this.fetchOrgAccessList(queryParams);
    } catch (error) {
      this.setState({ error });
    }
    this.setState({ showWarning: false });
  }

  handleWarning (roleName, roleId, resourceName, resourceId, type) {
    let warningTitle;
    let warningMsg;

    if (type === 'users') {
      warningTitle = i18nMark('User Access Removal');
      warningMsg = i18nMark(`Please confirm that you would like to remove ${roleName}
      access from ${resourceName}.`);
    }
    if (type === 'teams') {
      warningTitle = i18nMark('Team Access Removal');
      warningMsg = i18nMark(`Please confirm that you would like to remove ${roleName}
      access from the team ${resourceName}. This will affect all
      members of the team. If you would like to only remove access
      for this particular user, please remove them from the team.`);
    }

    this.setState({
      showWarning: true,
      warningMsg,
      warningTitle,
      deleteType: type,
      deleteRoleId: roleId,
      deleteResourceId: resourceId
    });
  }

  hideWarning () {
    this.setState({ showWarning: false });
  }

  confirmDelete () {
    const { deleteType, deleteResourceId, deleteRoleId } = this.state;
    this.removeRole(deleteRoleId, deleteResourceId, deleteType);
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
      warningMsg,
      warningTitle,
      showWarning
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
            {showWarning && (
              <Alert
                variant="danger"
                title={warningTitle}
                action={<AlertActionCloseButton onClose={this.hideWarning} />}
              >
                {warningMsg}
                <span style={buttonGroupStyle}>
                  <Button variant="danger" aria-label="confirm-delete" onClick={this.confirmDelete}>Delete</Button>
                  <Button variant="secondary" onClick={this.hideWarning}>Cancel</Button>
                </span>
              </Alert>
            )}

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
                                <Chip
                                  key={role.id}
                                  className="awx-c-chip"
                                  onClick={() => this.handleWarning(role.name, role.id, result.username, result.id, 'users')}
                                >
                                  {role.name}
                                </Chip>
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
                                <Chip
                                  key={role.id}
                                  className="awx-c-chip"
                                  onClick={() => this.handleWarning(role.name, role.id, role.team_name, role.team_id, 'teams')}
                                >
                                  {role.name}
                                </Chip>
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
  removeRole: PropTypes.func.isRequired,
};

export default AccessList;
