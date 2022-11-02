import React, { useState, useCallback } from 'react';
import { Route, Switch } from 'react-router-dom';

import { t } from '@lingui/macro';

import { Config } from 'contexts/Config';
import ScreenHeader from 'components/ScreenHeader';
import PersistentFilters from 'components/PersistentFilters';
import TeamList from './TeamList';
import TeamAdd from './TeamAdd';
import Team from './Team';

function Teams() {
  const [breadcrumbConfig, setBreadcrumbConfig] = useState({
    '/teams': t`Teams`,
    '/teams/add': t`Create New Team`,
  });

  const buildBreadcrumbConfig = useCallback((team) => {
    if (!team) {
      return;
    }

    setBreadcrumbConfig({
      '/teams': t`Teams`,
      '/teams/add': t`Create New Team`,
      [`/teams/${team.id}`]: `${team.name}`,
      [`/teams/${team.id}/edit`]: t`Edit Details`,
      [`/teams/${team.id}/details`]: t`Details`,
      [`/teams/${team.id}/users`]: t`Users`,
      [`/teams/${team.id}/access`]: t`Access`,
      [`/teams/${team.id}/roles`]: t`Roles`,
    });
  }, []);

  return (
    <>
      <ScreenHeader streamType="team" breadcrumbConfig={breadcrumbConfig} />
      <Switch>
        <Route path="/teams/add">
          <TeamAdd />
        </Route>
        <Route path="/teams/:id">
          <Team setBreadcrumb={buildBreadcrumbConfig} />
        </Route>
        <Route path="/teams">
          <PersistentFilters pageKey="teams">
            <Config>
              {({ me }) => <TeamList path="/teams" me={me || {}} />}
            </Config>
          </PersistentFilters>
        </Route>
      </Switch>
    </>
  );
}

export { Teams as _Teams };
export default Teams;
