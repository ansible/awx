import React from 'react';
import { Redirect, Route, Switch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { PageSection, Card } from '@patternfly/react-core';
import LoggingDetail from './LoggingDetail';
import LoggingEdit from './LoggingEdit';

function Logging({ i18n }) {
  const baseUrl = '/settings/logging';

  return (
    <PageSection>
      <Card>
        {i18n._(t`Logging settings`)}
        <Switch>
          <Redirect from={baseUrl} to={`${baseUrl}/details`} exact />
          <Route path={`${baseUrl}/details`}>
            <LoggingDetail />
          </Route>
          <Route path={`${baseUrl}/edit`}>
            <LoggingEdit />
          </Route>
        </Switch>
      </Card>
    </PageSection>
  );
}

export default withI18n()(Logging);
