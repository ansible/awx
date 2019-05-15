import React, { Component, Fragment } from 'react';
import { Route, withRouter, Switch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import { Config } from '../../contexts/Config';
import { NetworkProvider } from '../../contexts/Network';
import { withRootDialog } from '../../contexts/RootDialog';

import Breadcrumbs from '../../components/Breadcrumbs/Breadcrumbs';

import OrganizationsList from './screens/OrganizationsList';
import OrganizationAdd from './screens/OrganizationAdd';
import Organization from './screens/Organization/Organization';

class Organizations extends Component {
  constructor (props) {
    super(props);

    const { i18n } = props;

    this.state = {
      breadcrumbConfig: {
        '/organizations': i18n._(t`Organizations`),
        '/organizations/add': i18n._(t`Create New Organization`)
      }
    };
  }

  setBreadcrumbConfig = (organization) => {
    const { i18n } = this.props;

    if (!organization) {
      return;
    }

    const breadcrumbConfig = {
      '/organizations': i18n._(t`Organizations`),
      '/organizations/add': i18n._(t`Create New Organization`),
      [`/organizations/${organization.id}`]: `${organization.name}`,
      [`/organizations/${organization.id}/edit`]: i18n._(t`Edit Details`),
      [`/organizations/${organization.id}/details`]: i18n._(t`Details`),
      [`/organizations/${organization.id}/access`]: i18n._(t`Access`),
      [`/organizations/${organization.id}/teams`]: i18n._(t`Teams`),
      [`/organizations/${organization.id}/notifications`]: i18n._(t`Notifications`),
    };

    this.setState({ breadcrumbConfig });
  }

  render () {
    const { match, history, location, setRootDialogMessage, i18n } = this.props;
    const { breadcrumbConfig } = this.state;

    return (
      <Fragment>
        <Breadcrumbs
          breadcrumbConfig={breadcrumbConfig}
        />
        <Switch>
          <Route
            path={`${match.path}/add`}
            render={() => (
              <OrganizationAdd />
            )}
          />
          <Route
            path={`${match.path}/:id`}
            render={({ match: newRouteMatch }) => (
              <NetworkProvider
                handle404={() => {
                  history.replace('/organizations');
                  setRootDialogMessage({
                    title: '404',
                    bodyText: (
                      <Fragment>
                        {i18n._(t`Cannot find organization with ID`)}
                        <strong>{` ${newRouteMatch.params.id}`}</strong>
                        .
                      </Fragment>
                    ),
                    variant: 'warning'
                  });
                }}
              >
                <Config>
                  {({ me }) => (
                    <Organization
                      history={history}
                      location={location}
                      setBreadcrumb={this.setBreadcrumbConfig}
                      me={me || {}}
                    />
                  )}
                </Config>
              </NetworkProvider>
            )}
          />
          <Route
            path={`${match.path}`}
            render={() => (
              <OrganizationsList />
            )}
          />
        </Switch>
      </Fragment>
    );
  }
}

export { Organizations as _Organizations };
export default withI18n()(withRootDialog(withRouter(Organizations)));
