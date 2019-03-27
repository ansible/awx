import React, { Fragment } from 'react';
import PropTypes from 'prop-types';

import {
  DataList, DataListItem, DataListCell, Text,
  TextContent, TextVariants, Chip, Button
} from '@patternfly/react-core';

import {
  PlusIcon,
} from '@patternfly/react-icons';

import { I18n, i18nMark } from '@lingui/react';
import { t, Trans } from '@lingui/macro';

import {
  Link,
  withRouter
} from 'react-router-dom';

import { withNetwork } from '../../../contexts/Network';

import AlertModal from '../../../components/AlertModal';
import Pagination from '../../../components/Pagination';
import DataListToolbar from '../../../components/DataListToolbar';
import AddResourceRole from '../../../components/AddRole/AddResourceRole';

import {
  parseQueryString,
} from '../../../util/qs';

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

class OrganizationAccessList extends React.Component {
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
      count: 0,
      sortOrder: 'ascending',
      sortedColumnKey: 'username',
      showWarning: false,
      warningTitle: '',
      warningMsg: '',
      deleteType: '',
      deleteRoleId: null,
      deleteResourceId: null,
      results: [],
      isModalOpen: false
    };

    this.fetchOrgAccessList = this.fetchOrgAccessList.bind(this);
    this.onSetPage = this.onSetPage.bind(this);
    this.onSort = this.onSort.bind(this);
    this.getQueryParams = this.getQueryParams.bind(this);
    this.removeAccessRole = this.removeAccessRole.bind(this);
    this.handleWarning = this.handleWarning.bind(this);
    this.hideWarning = this.hideWarning.bind(this);
    this.confirmDelete = this.confirmDelete.bind(this);
    this.handleModalToggle = this.handleModalToggle.bind(this);
    this.handleSuccessfulRoleAdd = this.handleSuccessfulRoleAdd.bind(this);
  }

  componentDidMount () {
    const queryParams = this.getQueryParams();
    try {
      this.fetchOrgAccessList(queryParams);
    } catch (error) {
      this.setState({ error });
    }
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
    const { history } = this.props;
    const { search } = history.location;

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
        { count = 0, results = [] }
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

        result.teamRoles = teamRoles;
        result.userRoles = userRoles;
      });
      this.setState(stateToUpdate);
    } catch (error) {
      this.setState({ error });
    }
  }

  async removeAccessRole (roleId, resourceId, type) {
    const { removeRole, handleHttpError } = this.props;
    const url = `/api/v2/${type}/${resourceId}/roles/`;
    try {
      await removeRole(url, roleId);
      const queryParams = this.getQueryParams();
      await this.fetchOrgAccessList(queryParams);
      this.setState({ showWarning: false });
    } catch (error) {
      handleHttpError(error) || this.setState({ error });
    }
  }

  handleWarning (roleName, roleId, resourceName, resourceId, type) {
    let warningTitle;
    let warningMsg;

    if (type === 'users') {
      warningTitle = i18nMark('Remove User Access');
      warningMsg = (
        <Trans>
          Are you sure you want to remove
          <b>{` ${roleName} `}</b>
          access from
          <strong>{` ${resourceName}`}</strong>
          ?
        </Trans>
      );
    }
    if (type === 'teams') {
      warningTitle = i18nMark('Remove Team Access');
      warningMsg = (
        <Trans>
          Are you sure you want to remove
          <b>{` ${roleName} `}</b>
          access from
          <b>{` ${resourceName}`}</b>
          ?  Doing so affects all members of the team.
          <br />
          <br />
          If you
          <b><i> only </i></b>
          want to remove access for this particular user, please remove them from the team.
        </Trans>
      );
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

  handleSuccessfulRoleAdd () {
    this.handleModalToggle();
    const queryParams = this.getQueryParams();
    try {
      this.fetchOrgAccessList(queryParams);
    } catch (error) {
      this.setState({ error });
    }
  }

  handleModalToggle () {
    this.setState((prevState) => ({
      isModalOpen: !prevState.isModalOpen,
    }));
  }

  hideWarning () {
    this.setState({ showWarning: false });
  }

  confirmDelete () {
    const { deleteType, deleteResourceId, deleteRoleId } = this.state;
    this.removeAccessRole(deleteRoleId, deleteResourceId, deleteType);
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
      warningMsg,
      warningTitle,
      showWarning,
      isModalOpen
    } = this.state;
    const {
      api,
      organization
    } = this.props;
    return (
      <I18n>
        {({ i18n }) => (
          <Fragment>
            {!error && results.length <= 0 && (
              <h1>Loading...</h1> // TODO: replace with proper loading state
            )}
            {error && results.length <= 0 && (
              <Fragment>
                <div>{error.message}</div>
                {error.response && (
                  <div>{error.response.data.detail}</div>
                )}
              </Fragment> // TODO: replace with proper error handling
            )}
            {results.length > 0 && (
              <Fragment>
                <DataListToolbar
                  sortedColumnKey={sortedColumnKey}
                  sortOrder={sortOrder}
                  columns={this.columns}
                  onSearch={() => { }}
                  onSort={this.onSort}
                  add={(
                    <Fragment>
                      <Button
                        variant="primary"
                        aria-label={i18n._(t`Add Access Role`)}
                        onClick={this.handleModalToggle}
                      >
                        <PlusIcon />
                      </Button>
                      {isModalOpen && (
                        <AddResourceRole
                          onClose={this.handleModalToggle}
                          onSave={this.handleSuccessfulRoleAdd}
                          api={api}
                          roles={organization.summary_fields.object_roles}
                        />
                      )}
                    </Fragment>
                  )}
                />
                {showWarning && (
                  <AlertModal
                    variant="danger"
                    title={warningTitle}
                    isOpen={showWarning}
                    onClose={this.hideWarning}
                    actions={[
                      <Button key="delete" variant="danger" aria-label="Confirm delete" onClick={this.confirmDelete}>{i18n._(t`Delete`)}</Button>,
                      <Button key="cancel" variant="secondary" onClick={this.hideWarning}>{i18n._(t`Cancel`)}</Button>
                    ]}
                  >
                    {warningMsg}
                  </AlertModal>
                )}
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
                            customStyles={null}
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
                          customStyles={null}
                        />
                        {result.userRoles.length > 0 && (
                          <ul style={userRolesWrapperStyle}>
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
                          <ul style={userRolesWrapperStyle}>
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
        )}
      </I18n>
    );
  }
}

OrganizationAccessList.propTypes = {
  getAccessList: PropTypes.func.isRequired,
  removeRole: PropTypes.func.isRequired
};

export { OrganizationAccessList as _OrganizationAccessList };
export default withRouter(withNetwork(OrganizationAccessList));
