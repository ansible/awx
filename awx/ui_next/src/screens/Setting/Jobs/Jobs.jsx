import React from 'react';
import { Redirect, Route, Switch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { PageSection, Card } from '@patternfly/react-core';
import JobsDetail from './JobsDetail';
import JobsEdit from './JobsEdit';

function Jobs({ i18n }) {
  const baseUrl = '/settings/jobs';

  return (
    <PageSection>
      <Card>
        {i18n._(t`Jobs settings`)}
        <Switch>
          <Redirect from={baseUrl} to={`${baseUrl}/details`} exact />
          <Route path={`${baseUrl}/details`}>
            <JobsDetail />
          </Route>
          <Route path={`${baseUrl}/edit`}>
            <JobsEdit />
          </Route>
        </Switch>
      </Card>
    </PageSection>
  );
}

export default withI18n()(Jobs);
