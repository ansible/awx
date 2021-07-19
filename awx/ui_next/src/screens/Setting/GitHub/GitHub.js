import React from 'react';
import { Link, Redirect, Route, Switch, useRouteMatch } from 'react-router-dom';

import { t } from '@lingui/macro';
import { PageSection, Card } from '@patternfly/react-core';
import ContentError from 'components/ContentError';
import GitHubDetail from './GitHubDetail';
import GitHubEdit from './GitHubEdit';
import GitHubOrgEdit from './GitHubOrgEdit';
import GitHubTeamEdit from './GitHubTeamEdit';
import GitHubEnterpriseEdit from './GitHubEnterpriseEdit';
import GitHubEnterpriseOrgEdit from './GitHubEnterpriseOrgEdit';
import GitHubEnterpriseTeamEdit from './GitHubEnterpriseTeamEdit';

function GitHub() {
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
          <Route path={`${baseURL}/default/edit`}>
            <GitHubEdit />
          </Route>
          <Route path={`${baseURL}/organization/edit`}>
            <GitHubOrgEdit />
          </Route>
          <Route path={`${baseURL}/team/edit`}>
            <GitHubTeamEdit />
          </Route>
          <Route path={`${baseURL}/enterprise/edit`}>
            <GitHubEnterpriseEdit />
          </Route>
          <Route path={`${baseURL}/enterprise_organization/edit`}>
            <GitHubEnterpriseOrgEdit />
          </Route>
          <Route path={`${baseURL}/enterprise_team/edit`}>
            <GitHubEnterpriseTeamEdit />
          </Route>
          <Route key="not-found" path={`${baseURL}/*`}>
            <ContentError isNotFound>
              <Link to={`${baseURL}/default/details`}>
                {t`View GitHub Settings`}
              </Link>
            </ContentError>
          </Route>
        </Switch>
      </Card>
    </PageSection>
  );
}

export default GitHub;
