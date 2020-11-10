import React, { Component, Fragment } from 'react';
import { Route, withRouter, Switch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import { Config } from '../../contexts/Config';
import Breadcrumbs from '../../components/Breadcrumbs/Breadcrumbs';

import OrganizationsList from './OrganizationList/OrganizationList';
import OrganizationAdd from './OrganizationAdd/OrganizationAdd';
import Organization from './Organization';

class Organizations extends Component {
  constructor(props) {
    super(props);

    const { i18n } = props;

    this.state = {
      breadcrumbConfig: {
        '/organizations': i18n._(t`Organizations`),
        '/organizations/add': i18n._(t`Create New Organization`),
      },
    };
  }

  setBreadcrumbConfig = organization => {
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
      [`/organizations/${organization.id}/notifications`]: i18n._(
        t`Notifications`
      ),
    };

    this.setState({ breadcrumbConfig });
  };

  render() {
    const { match } = this.props;
    const { breadcrumbConfig } = this.state;

    return (
      <Fragment>
        <Breadcrumbs breadcrumbConfig={breadcrumbConfig} />
        <Switch>
          <Route path={`${match.path}/add`}>
            <OrganizationAdd />
          </Route>
          <Route path={`${match.path}/:id`}>
            <Config>
              {({ me }) => (
                <Organization
                  setBreadcrumb={this.setBreadcrumbConfig}
                  me={me || {}}
                />
              )}
            </Config>
          </Route>
          <Route path={`${match.path}`}>
            <OrganizationsList />
          </Route>
        </Switch>
      </Fragment>
    );
  }
}

export { Organizations as _Organizations };
export default withI18n()(withRouter(Organizations));
