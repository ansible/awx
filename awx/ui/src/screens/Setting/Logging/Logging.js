import React from 'react';
import { Link, Redirect, Route, Switch } from 'react-router-dom';

import { t } from '@lingui/macro';
import { PageSection, Card } from '@patternfly/react-core';
import ContentError from 'components/ContentError';
import { useConfig } from 'contexts/Config';
import LoggingDetail from './LoggingDetail';
import LoggingEdit from './LoggingEdit';

function Logging() {
  const baseURL = '/settings/logging';
  const { me } = useConfig();

  return (
    <PageSection>
      <Card>
        <Switch>
          <Redirect from={baseURL} to={`${baseURL}/details`} exact />
          <Route path={`${baseURL}/details`}>
            <LoggingDetail />
          </Route>
          <Route path={`${baseURL}/edit`}>
            {me?.is_superuser ? (
              <LoggingEdit />
            ) : (
              <Redirect to={`${baseURL}/details`} />
            )}
          </Route>
          <Route key="not-found" path={`${baseURL}/*`}>
            <ContentError isNotFound>
              <Link to={`${baseURL}/details`}>{t`View Logging settings`}</Link>
            </ContentError>
          </Route>
        </Switch>
      </Card>
    </PageSection>
  );
}

export default Logging;
