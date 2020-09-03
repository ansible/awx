import React, { useState, useCallback } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Route, Switch } from 'react-router-dom';

import ApplicationsList from './ApplicationsList';
import ApplicationAdd from './ApplicationAdd';
import Application from './Application';
import Breadcrumbs from '../../components/Breadcrumbs';

function Applications({ i18n }) {
  const [breadcrumbConfig, setBreadcrumbConfig] = useState({
    '/applications': i18n._(t`Applications`),
    '/applications/add': i18n._(t`Create New Application`),
  });

  const buildBreadcrumbConfig = useCallback(
    application => {
      if (!application) {
        return;
      }
      setBreadcrumbConfig({
        '/applications': i18n._(t`Applications`),
        '/applications/add': i18n._(t`Create New Application`),
        [`/applications/${application.id}`]: `${application.name}`,
        [`/applications/${application.id}/edit`]: i18n._(t`Edit Details`),
        [`/applications/${application.id}/details`]: i18n._(t`Details`),
        [`/applications/${application.id}/tokens`]: i18n._(t`Tokens`),
      });
    },
    [i18n]
  );

  return (
    <>
      <Breadcrumbs breadcrumbConfig={breadcrumbConfig} />
      <Switch>
        <Route path="/applications/add">
          <ApplicationAdd />
        </Route>
        <Route path="/applications/:id">
          <Application setBreadcrumb={buildBreadcrumbConfig} />
        </Route>
        <Route path="/applications">
          <ApplicationsList />
        </Route>
      </Switch>
    </>
  );
}

export default withI18n()(Applications);
