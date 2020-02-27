import React, { useState, useCallback } from 'react';
import {
  Route,
  Switch,
  useHistory,
  useLocation,
  useRouteMatch,
} from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { PageSection } from '@patternfly/react-core';
import Breadcrumbs from '@components/Breadcrumbs/Breadcrumbs';
import Job from './Job';
import JobTypeRedirect from './JobTypeRedirect';
import JobList from '@components/JobList';
import { JOB_TYPE_URL_SEGMENTS } from '@constants';

function Jobs({ i18n }) {
  const history = useHistory();
  const location = useLocation();
  const match = useRouteMatch();
  const [breadcrumbConfig, setBreadcrumbConfig] = useState({
    '/jobs': i18n._(t`Jobs`),
  });

  const buildBreadcrumbConfig = useCallback(
    job => {
      if (!job) {
        return;
      }

      const type = JOB_TYPE_URL_SEGMENTS[job.type];
      setBreadcrumbConfig({
        '/jobs': i18n._(t`Jobs`),
        [`/jobs/${type}/${job.id}`]: `${job.name}`,
        [`/jobs/${type}/${job.id}/output`]: i18n._(t`Output`),
        [`/jobs/${type}/${job.id}/details`]: i18n._(t`Details`),
      });
    },
    [i18n]
  );

  return (
    <>
      <Breadcrumbs breadcrumbConfig={breadcrumbConfig} />
      <Switch>
        <Route exact path={match.path}>
          <PageSection>
            <JobList
              showTypeColumn
              defaultParams={{ not__launch_type: 'sync' }}
            />
          </PageSection>
        </Route>
        <Route
          path={`${match.path}/:id/details`}
          render={({ match: m }) => (
            <JobTypeRedirect id={m.params.id} path={m.path} view="details" />
          )}
        />
        <Route
          path={`${match.path}/:id/output`}
          render={({ match: m }) => (
            <JobTypeRedirect id={m.params.id} path={m.path} view="output" />
          )}
        />
        <Route
          path={`${match.path}/:type/:id`}
          render={() => (
            <Job
              history={history}
              location={location}
              setBreadcrumb={buildBreadcrumbConfig}
            />
          )}
        />
        <Route
          path={`${match.path}/:id`}
          render={({ match: m }) => (
            <JobTypeRedirect id={m.params.id} path={m.path} />
          )}
        />
      </Switch>
    </>
  );
}

export { Jobs as _Jobs };
export default withI18n()(Jobs);
