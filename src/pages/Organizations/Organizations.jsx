import React, { Component, Fragment } from 'react';
import { Route, withRouter, Switch } from 'react-router-dom';
import { i18nMark } from '@lingui/react';

import { NetworkProvider } from '../../contexts/Network';
import { withRootDialog } from '../../contexts/RootDialog';

import Breadcrumbs from '../../components/Breadcrumbs/Breadcrumbs';

import OrganizationsList from './screens/OrganizationsList';
import OrganizationAdd from './screens/OrganizationAdd';
import Organization from './screens/Organization/Organization';

class Organizations extends Component {
  state = {
    breadcrumbConfig: {
      '/organizations': i18nMark('Organizations'),
      '/organizations/add': i18nMark('Create New Organization')
    }
  };

  setBreadcrumbConfig = (organization) => {
    if (!organization) {
      return;
    }

    const breadcrumbConfig = {
      '/organizations': i18nMark('Organizations'),
      '/organizations/add': i18nMark('Create New Organization'),
      [`/organizations/${organization.id}`]: `${organization.name}`,
      [`/organizations/${organization.id}/edit`]: i18nMark('Edit Details'),
      [`/organizations/${organization.id}/details`]: i18nMark('Details'),
      [`/organizations/${organization.id}/access`]: i18nMark('Access'),
      [`/organizations/${organization.id}/teams`]: i18nMark('Teams'),
      [`/organizations/${organization.id}/notifications`]: i18nMark('Notifications'),
    };

    this.setState({ breadcrumbConfig });
  }

  render () {
    const { match, history, location, setRootDialogMessage } = this.props;
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
                    bodyText: `Cannot find organization with ID ${newRouteMatch.params.id}.`,
                    variant: 'warning'
                  });
                }}
              >
                <Organization
                  history={history}
                  location={location}
                  setBreadcrumb={this.setBreadcrumbConfig}
                />
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

export default withRootDialog(withRouter(Organizations));
