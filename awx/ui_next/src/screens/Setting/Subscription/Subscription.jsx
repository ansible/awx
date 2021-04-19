import React from 'react';
import { Link, Redirect, Route, Switch, useRouteMatch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { PageSection, Card } from '@patternfly/react-core';
import SubscriptionDetail from './SubscriptionDetail';
import SubscriptionEdit from './SubscriptionEdit';
import ContentError from '../../../components/ContentError';

function Subscription({ i18n }) {
  const baseURL = '/settings/subscription';
  const baseRoute = useRouteMatch({
    path: '/settings/subscription',
    exact: true,
  });

  return (
    <PageSection>
      <Card>
        {baseRoute && <Redirect to={`${baseURL}/details`} />}
        <Switch>
          <Route path={`${baseURL}/details`}>
            <SubscriptionDetail />
          </Route>
          <Route path={`${baseURL}/edit`}>
            <SubscriptionEdit />
          </Route>
          <Route key="not-found" path={`${baseURL}/*`}>
            <ContentError isNotFound>
              <Link to={baseURL}>{i18n._(t`View Settings`)}</Link>
            </ContentError>
          </Route>
        </Switch>
      </Card>
    </PageSection>
  );
}

export default withI18n()(Subscription);
