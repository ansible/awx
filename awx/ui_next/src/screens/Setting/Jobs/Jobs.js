import React from 'react';
import { Link, Redirect, Route, Switch } from 'react-router-dom';

import { t } from '@lingui/macro';
import { PageSection, Card } from '@patternfly/react-core';
import ContentError from 'components/ContentError';
import JobsDetail from './JobsDetail';
import JobsEdit from './JobsEdit';

function Jobs() {
  const baseURL = '/settings/jobs';
  return (
    <PageSection>
      <Card>
        <Switch>
          <Redirect from={baseURL} to={`${baseURL}/details`} exact />
          <Route path={`${baseURL}/details`}>
            <JobsDetail />
          </Route>
          <Route path={`${baseURL}/edit`}>
            <JobsEdit />
          </Route>
          <Route key="not-found" path={`${baseURL}/*`}>
            <ContentError isNotFound>
              <Link to={`${baseURL}/details`}>{t`View Jobs settings`}</Link>
            </ContentError>
          </Route>
        </Switch>
      </Card>
    </PageSection>
  );
}

export default Jobs;
