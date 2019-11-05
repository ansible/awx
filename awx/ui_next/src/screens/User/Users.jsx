import React, { Component, Fragment } from 'react';
import { Route, withRouter, Switch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import { Config } from '@contexts/Config';
import Breadcrumbs from '@components/Breadcrumbs/Breadcrumbs';

import UsersList from './UserList/UserList';
import UserAdd from './UserAdd/UserAdd';
import User from './User';

class Users extends Component {
  constructor(props) {
    super(props);

    const { i18n } = props;

    this.state = {
      breadcrumbConfig: {
        '/users': i18n._(t`Users`),
        '/users/add': i18n._(t`Create New User`),
      },
    };
  }

  setBreadcrumbConfig = user => {
    const { i18n } = this.props;

    if (!user) {
      return;
    }

    const breadcrumbConfig = {
      '/users': i18n._(t`Users`),
      '/users/add': i18n._(t`Create New User`),
      [`/users/${user.id}`]: `${user.username}`,
      [`/users/${user.id}/edit`]: i18n._(t`Edit Details`),
      [`/users/${user.id}/details`]: i18n._(t`Details`),
      [`/users/${user.id}/access`]: i18n._(t`Access`),
      [`/users/${user.id}/teams`]: i18n._(t`Teams`),
      [`/users/${user.id}/organizations`]: i18n._(t`Organizations`),
      [`/users/${user.id}/tokens`]: i18n._(t`Tokens`),
    };

    this.setState({ breadcrumbConfig });
  };

  render() {
    const { match, history, location } = this.props;
    const { breadcrumbConfig } = this.state;

    return (
      <Fragment>
        <Breadcrumbs breadcrumbConfig={breadcrumbConfig} />
        <Switch>
          <Route path={`${match.path}/add`} render={() => <UserAdd />} />
          <Route
            path={`${match.path}/:id`}
            render={() => (
              <Config>
                {({ me }) => (
                  <User
                    history={history}
                    location={location}
                    setBreadcrumb={this.setBreadcrumbConfig}
                    me={me || {}}
                  />
                )}
              </Config>
            )}
          />
          <Route path={`${match.path}`} render={() => <UsersList />} />
        </Switch>
      </Fragment>
    );
  }
}

export { Users as _Users };
export default withI18n()(withRouter(Users));
