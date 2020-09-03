import React from 'react';
import { Redirect, Route, Switch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { PageSection, Card } from '@patternfly/react-core';
import GitHubDetail from './GitHubDetail';
import GitHubEdit from './GitHubEdit';

function GitHub({ i18n }) {
  const baseUrl = '/settings/github';

  return (
    <PageSection>
      <Card>
        {i18n._(t`GitHub settings`)}
        <Switch>
          <Redirect from={baseUrl} to={`${baseUrl}/details`} exact />
          <Route path={`${baseUrl}/details`}>
            <GitHubDetail />
          </Route>
          <Route path={`${baseUrl}/edit`}>
            <GitHubEdit />
          </Route>
        </Switch>
      </Card>
    </PageSection>
  );
}

export default withI18n()(GitHub);
