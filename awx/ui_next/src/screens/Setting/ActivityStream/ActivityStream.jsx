import React from 'react';
import { Link, Redirect, Route, Switch } from 'react-router-dom';

import { t } from '@lingui/macro';
import { PageSection, Card } from '@patternfly/react-core';
import ContentError from '../../../components/ContentError';
import { useConfig } from '../../../contexts/Config';
import ActivityStreamDetail from './ActivityStreamDetail';
import ActivityStreamEdit from './ActivityStreamEdit';

function ActivityStream() {
  const baseURL = '/settings/activity_stream';
  const { me } = useConfig();

  return (
    <PageSection>
      <Card>
        <Switch>
          <Redirect from={baseURL} to={`${baseURL}/details`} exact />
          <Route path={`${baseURL}/details`}>
            <ActivityStreamDetail />
          </Route>
          <Route path={`${baseURL}/edit`}>
            {me?.is_superuser ? (
              <ActivityStreamEdit />
            ) : (
              <Redirect to={`${baseURL}/details`} />
            )}
          </Route>
          <Route key="not-found" path={`${baseURL}/*`}>
            <ContentError isNotFound>
              <Link to={`${baseURL}/details`}>
                {t`View Activity Stream settings`}
              </Link>
            </ContentError>
          </Route>
        </Switch>
      </Card>
    </PageSection>
  );
}

export default ActivityStream;
