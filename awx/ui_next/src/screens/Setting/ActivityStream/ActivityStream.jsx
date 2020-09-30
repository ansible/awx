import React from 'react';
import { Link, Redirect, Route, Switch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { PageSection, Card } from '@patternfly/react-core';
import ContentError from '../../../components/ContentError';
import ActivityStreamDetail from './ActivityStreamDetail';
import ActivityStreamEdit from './ActivityStreamEdit';

function ActivityStream({ i18n }) {
  const baseURL = '/settings/activity_stream';
  return (
    <PageSection>
      <Card>
        <Switch>
          <Redirect from={baseURL} to={`${baseURL}/details`} exact />
          <Route path={`${baseURL}/details`}>
            <ActivityStreamDetail />
          </Route>
          <Route path={`${baseURL}/edit`}>
            <ActivityStreamEdit />
          </Route>
          <Route key="not-found" path={`${baseURL}/*`}>
            <ContentError isNotFound>
              <Link to={`${baseURL}/details`}>
                {i18n._(t`View Activity Stream settings`)}
              </Link>
            </ContentError>
          </Route>
        </Switch>
      </Card>
    </PageSection>
  );
}

export default withI18n()(ActivityStream);
