import React, { Component, Fragment } from 'react';
import { withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Card, PageSection } from '@patternfly/react-core';

import { UsersAPI } from '@api';
import AlertModal from '@components/AlertModal';
import DataListToolbar from '@components/DataListToolbar';
import ErrorDetail from '@components/ErrorDetail';
import PaginatedDataList, {
  ToolbarAddButton,
  ToolbarDeleteButton,
} from '@components/PaginatedDataList';
import { getQSConfig, parseQueryString } from '@util/qs';

import UserListItem from './UserListItem';

const QS_CONFIG = getQSConfig('user', {
  page: 1,
  page_size: 20,
  order_by: 'username',
});

class UsersList extends Component {
  constructor(props) {
    super(props);

    this.state = {
      hasContentLoading: true,
      contentError: null,
      deletionError: null,
      users: [],
      selected: [],
      itemCount: 0,
      actions: null,
    };

    this.handleSelectAll = this.handleSelectAll.bind(this);
    this.handleSelect = this.handleSelect.bind(this);
    this.handleUserDelete = this.handleUserDelete.bind(this);
    this.handleDeleteErrorClose = this.handleDeleteErrorClose.bind(this);
    this.loadUsers = this.loadUsers.bind(this);
  }

  componentDidMount() {
    this.loadUsers();
  }

  componentDidUpdate(prevProps) {
    const { location } = this.props;
    if (location !== prevProps.location) {
      this.loadUsers();
    }
  }

  handleSelectAll(isSelected) {
    const { users } = this.state;

    const selected = isSelected ? [...users] : [];
    this.setState({ selected });
  }

  handleSelect(row) {
    const { selected } = this.state;

    if (selected.some(s => s.id === row.id)) {
      this.setState({ selected: selected.filter(s => s.id !== row.id) });
    } else {
      this.setState({ selected: selected.concat(row) });
    }
  }

  handleDeleteErrorClose() {
    this.setState({ deletionError: null });
  }

  async handleUserDelete() {
    const { selected } = this.state;

    this.setState({ hasContentLoading: true });
    try {
      await Promise.all(selected.map(org => UsersAPI.destroy(org.id)));
    } catch (err) {
      this.setState({ deletionError: err });
    } finally {
      await this.loadUsers();
    }
  }

  async loadUsers() {
    const { location } = this.props;
    const { actions: cachedActions } = this.state;
    const params = parseQueryString(QS_CONFIG, location.search);

    let optionsPromise;
    if (cachedActions) {
      optionsPromise = Promise.resolve({ data: { actions: cachedActions } });
    } else {
      optionsPromise = UsersAPI.readOptions();
    }

    const promises = Promise.all([UsersAPI.read(params), optionsPromise]);

    this.setState({ contentError: null, hasContentLoading: true });
    try {
      const [
        {
          data: { count, results },
        },
        {
          data: { actions },
        },
      ] = await promises;
      this.setState({
        actions,
        itemCount: count,
        users: results,
        selected: [],
      });
    } catch (err) {
      this.setState({ contentError: err });
    } finally {
      this.setState({ hasContentLoading: false });
    }
  }

  render() {
    const {
      actions,
      itemCount,
      contentError,
      hasContentLoading,
      deletionError,
      selected,
      users,
    } = this.state;
    const { match, i18n } = this.props;

    const canAdd =
      actions && Object.prototype.hasOwnProperty.call(actions, 'POST');
    const isAllSelected =
      selected.length === users.length && selected.length > 0;

    return (
      <Fragment>
        <PageSection>
          <Card>
            <PaginatedDataList
              contentError={contentError}
              hasContentLoading={hasContentLoading}
              items={users}
              itemCount={itemCount}
              pluralizedItemName="Users"
              qsConfig={QS_CONFIG}
              onRowClick={this.handleSelect}
              toolbarSearchColumns={[
                {
                  name: i18n._(t`Username`),
                  key: 'username',
                  isDefault: true,
                },
                {
                  name: i18n._(t`First Name`),
                  key: 'first_name',
                },
                {
                  name: i18n._(t`Last Name`),
                  key: 'last_name',
                },
              ]}
              toolbarSortColumns={[
                {
                  name: i18n._(t`Username`),
                  key: 'username',
                },
                {
                  name: i18n._(t`First Name`),
                  key: 'first_name',
                },
                {
                  name: i18n._(t`Last Name`),
                  key: 'last_name',
                },
              ]}
              renderToolbar={props => (
                <DataListToolbar
                  {...props}
                  showSelectAll
                  isAllSelected={isAllSelected}
                  onSelectAll={this.handleSelectAll}
                  qsConfig={QS_CONFIG}
                  additionalControls={[
                    ...(canAdd
                      ? [
                          <ToolbarAddButton
                            key="add"
                            linkTo={`${match.url}/add`}
                          />,
                        ]
                      : []),
                    <ToolbarDeleteButton
                      key="delete"
                      onDelete={this.handleUserDelete}
                      itemsToDelete={selected}
                      pluralizedItemName="Users"
                    />,
                  ]}
                />
              )}
              renderItem={o => (
                <UserListItem
                  key={o.id}
                  user={o}
                  detailUrl={`${match.url}/${o.id}`}
                  isSelected={selected.some(row => row.id === o.id)}
                  onSelect={() => this.handleSelect(o)}
                />
              )}
              emptyStateControls={
                canAdd ? (
                  <ToolbarAddButton key="add" linkTo={`${match.url}/add`} />
                ) : null
              }
            />
          </Card>
        </PageSection>
        <AlertModal
          isOpen={deletionError}
          variant="error"
          title={i18n._(t`Error!`)}
          onClose={this.handleDeleteErrorClose}
        >
          {i18n._(t`Failed to delete one or more users.`)}
          <ErrorDetail error={deletionError} />
        </AlertModal>
      </Fragment>
    );
  }
}

export { UsersList as _UsersList };
export default withI18n()(withRouter(UsersList));
