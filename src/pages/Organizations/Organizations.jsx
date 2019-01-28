import React, { Component, Fragment } from 'react';
import { Route, Switch } from 'react-router-dom';
import { i18nMark } from '@lingui/react';

import OrganizationsList from './screens/OrganizationsList';
import OrganizationAdd from './screens/OrganizationAdd';
import Organization from './screens/Organization/Organization';
import Breadcrumbs from '../../components/Breadcrumbs/Breadcrumbs';

class Organizations extends Component {
  state = {
    breadcrumbConfig: {
      '/organizations': i18nMark('Organizations'),
      '/organizations/add': i18nMark('Create New Organization')
    }
  }

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
    const { match, api, history, location } = this.props;
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
              <OrganizationAdd
                api={api}
              />
            )}
          />
          <Route
            path={`${match.path}/:id`}
            render={() => (
              <Organization
                api={api}
                history={history}
                location={location}
                setBreadcrumb={this.setBreadcrumbConfig}
              />
            )}
          />
          <Route
            path={`${match.path}`}
            render={() => (
              <OrganizationsList
                api={api}
              />
            )}
          />
        </Switch>
      </Fragment>
    );
  }
}

export default Organizations;
