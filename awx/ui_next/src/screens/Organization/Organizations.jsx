import React, { useCallback, useState, Fragment } from 'react';
import { Route, withRouter, Switch, useRouteMatch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import { Config } from '../../contexts/Config';
import ScreenHeader from '../../components/ScreenHeader/ScreenHeader';

import OrganizationsList from './OrganizationList/OrganizationList';
import OrganizationAdd from './OrganizationAdd/OrganizationAdd';
import Organization from './Organization';

function Organizations({ i18n }) {
  const match = useRouteMatch();
  const [breadcrumbConfig, setBreadcrumbConfig] = useState({
    '/organizations': i18n._(t`Organizations`),
    '/organizations/add': i18n._(t`Create New Organization`),
  });

  const setBreadcrumb = useCallback(
    organization => {
      if (!organization) {
        return;
      }

      const breadcrumb = {
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
      setBreadcrumbConfig(breadcrumb);
    },
    [i18n]
  );

  return (
    <Fragment>
      <ScreenHeader
        streamType="organization"
        breadcrumbConfig={breadcrumbConfig}
      />
      <Switch>
        <Route path={`${match.path}/add`}>
          <OrganizationAdd />
        </Route>
        <Route path={`${match.path}/:id`}>
          <Config>
            {({ me }) => (
              <Organization setBreadcrumb={setBreadcrumb} me={me || {}} />
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

export { Organizations as _Organizations };
export default withI18n()(withRouter(Organizations));
