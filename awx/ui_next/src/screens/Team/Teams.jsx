import React, { Component, Fragment } from 'react';
import { Route, withRouter, Switch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import { Config } from '@contexts/Config';
import Breadcrumbs from '@components/Breadcrumbs/Breadcrumbs';

import TeamsList from './TeamList/TeamList';
import TeamAdd from './TeamAdd/TeamAdd';
import Team from './Team';

class Teams extends Component {
  constructor(props) {
    super(props);

    const { i18n } = props;

    this.state = {
      breadcrumbConfig: {
        '/teams': i18n._(t`Teams`),
        '/teams/add': i18n._(t`Create New Team`),
      },
    };
  }

  setBreadcrumbConfig = team => {
    const { i18n } = this.props;

    if (!team) {
      return;
    }

    const breadcrumbConfig = {
      '/teams': i18n._(t`Teams`),
      '/teams/add': i18n._(t`Create New Team`),
      [`/teams/${team.id}`]: `${team.name}`,
      [`/teams/${team.id}/edit`]: i18n._(t`Edit Details`),
      [`/teams/${team.id}/details`]: i18n._(t`Details`),
      [`/teams/${team.id}/users`]: i18n._(t`Users`),
      [`/teams/${team.id}/access`]: i18n._(t`Access`),
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
          <Route path={`${match.path}/add`} render={() => <TeamAdd />} />
          <Route
            path={`${match.path}/:id`}
            render={() => (
              <Config>
                {({ me }) => (
                  <Team
                    history={history}
                    location={location}
                    setBreadcrumb={this.setBreadcrumbConfig}
                    me={me || {}}
                  />
                )}
              </Config>
            )}
          />
          <Route path={`${match.path}`} render={() => <TeamsList />} />
        </Switch>
      </Fragment>
    );
  }
}

export { Teams as _Teams };
export default withI18n()(withRouter(Teams));
