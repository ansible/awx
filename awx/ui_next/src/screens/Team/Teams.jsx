import React, { useState, useCallback } from 'react';
import { Route, Switch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import { Config } from '../../contexts/Config';
import Breadcrumbs from '../../components/Breadcrumbs';
import TeamList from './TeamList';
import TeamAdd from './TeamAdd';
import Team from './Team';

function Teams({ i18n }) {
  const [breadcrumbConfig, setBreadcrumbConfig] = useState({
    '/teams': i18n._(t`Teams`),
    '/teams/add': i18n._(t`Create New Team`),
  });

  const buildBreadcrumbConfig = useCallback(
    team => {
      if (!team) {
        return;
      }

      setBreadcrumbConfig({
        '/teams': i18n._(t`Teams`),
        '/teams/add': i18n._(t`Create New Team`),
        [`/teams/${team.id}`]: `${team.name}`,
        [`/teams/${team.id}/edit`]: i18n._(t`Edit Details`),
        [`/teams/${team.id}/details`]: i18n._(t`Details`),
        [`/teams/${team.id}/users`]: i18n._(t`Users`),
        [`/teams/${team.id}/access`]: i18n._(t`Access`),
      });
    },
    [i18n]
  );

  return (
    <>
      <Breadcrumbs breadcrumbConfig={breadcrumbConfig} />
      <Switch>
        <Route path="/teams/add">
          <TeamAdd />
        </Route>
        <Route path="/teams/:id">
          <Team setBreadcrumb={buildBreadcrumbConfig} />
        </Route>
        <Route path="/teams">
          <Config>
            {({ me }) => <TeamList path="/teams" me={me || {}} />}
          </Config>
        </Route>
      </Switch>
    </>
  );
}

export { Teams as _Teams };
export default withI18n()(Teams);
