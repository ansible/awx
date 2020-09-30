import React from 'react';
import { Link, Redirect, Route, Switch, useRouteMatch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { PageSection, Card } from '@patternfly/react-core';
import ContentError from '../../../components/ContentError';
import GitHubDetail from './GitHubDetail';
import GitHubEdit from './GitHubEdit';

function GitHub({ i18n }) {
  const baseURL = '/settings/github';
  const baseRoute = useRouteMatch({ path: '/settings/github', exact: true });
  const categoryRoute = useRouteMatch({
    path: '/settings/github/:category',
    exact: true,
  });

  return (
    <PageSection>
      <Card>
        <Switch>
          {baseRoute && <Redirect to={`${baseURL}/default/details`} exact />}
          {categoryRoute && (
            <Redirect
              to={`${baseURL}/${categoryRoute.params.category}/details`}
              exact
            />
          )}
          <Route path={`${baseURL}/:category/details`}>
            <GitHubDetail />
          </Route>
          <Route path={`${baseURL}/:category/edit`}>
            <GitHubEdit />
          </Route>
          <Route key="not-found" path={`${baseURL}/*`}>
            <ContentError isNotFound>
              <Link to={`${baseURL}/default/details`}>
                {i18n._(t`View GitHub Settings`)}
              </Link>
            </ContentError>
          </Route>
        </Switch>
      </Card>
    </PageSection>
  );
}

export default withI18n()(GitHub);
