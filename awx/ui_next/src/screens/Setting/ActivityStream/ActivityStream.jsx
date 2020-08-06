import React from 'react';
import { Redirect, Route, Switch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { PageSection, Card } from '@patternfly/react-core';
import ActivityStreamDetail from './ActivityStreamDetail';
import ActivityStreamEdit from './ActivityStreamEdit';

function ActivityStream({ i18n }) {
  const baseUrl = '/settings/activity_stream';
  return (
    <PageSection>
      <Card>
        {i18n._(t`Activity stream settings`)}
        <Switch>
          <Redirect from={baseUrl} to={`${baseUrl}/details`} exact />
          <Route path={`${baseUrl}/details`}>
            <ActivityStreamDetail />
          </Route>
          <Route path={`${baseUrl}/edit`}>
            <ActivityStreamEdit />
          </Route>
        </Switch>
      </Card>
    </PageSection>
  );
}

export default withI18n()(ActivityStream);
