import React, { useCallback, useState } from 'react';
import { Route, withRouter, Switch, useRouteMatch } from 'react-router-dom';

import { t } from '@lingui/macro';

import { Config } from 'contexts/Config';
import ScreenHeader from 'components/ScreenHeader/ScreenHeader';
import PersistentFilters from 'components/PersistentFilters';
import OrganizationsList from './OrganizationList/OrganizationList';
import OrganizationAdd from './OrganizationAdd/OrganizationAdd';
import Organization from './Organization';

function Organizations() {
  const match = useRouteMatch();
  const [breadcrumbConfig, setBreadcrumbConfig] = useState({
    '/organizations': t`Organizations`,
    '/organizations/add': t`Create New Organization`,
  });

  const setBreadcrumb = useCallback((organization) => {
    if (!organization) {
      return;
    }

    const breadcrumb = {
      '/organizations': t`Organizations`,
      '/organizations/add': t`Create New Organization`,
      [`/organizations/${organization.id}`]: `${organization.name}`,
      [`/organizations/${organization.id}/edit`]: t`Edit Details`,
      [`/organizations/${organization.id}/details`]: t`Details`,
      [`/organizations/${organization.id}/access`]: t`Access`,
      [`/organizations/${organization.id}/teams`]: t`Teams`,
      [`/organizations/${organization.id}/notifications`]: t`Notifications`,
      [`/organizations/${organization.id}/execution_environments`]: t`Execution Environments`,
    };
    setBreadcrumbConfig(breadcrumb);
  }, []);

  return (
    <>
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
          <PersistentFilters pageKey="organizations">
            <OrganizationsList />
          </PersistentFilters>
        </Route>
      </Switch>
    </>
  );
}

export { Organizations as _Organizations };
export default withRouter(Organizations);
