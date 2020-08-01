import React, { useState, useCallback } from 'react';
import {
  Route,
  Switch,
  useHistory,
  useLocation,
  useParams,
  useRouteMatch,
} from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { PageSection } from '@patternfly/react-core';
import Breadcrumbs from '../../components/Breadcrumbs/Breadcrumbs';
import Job from './Job';
import JobTypeRedirect from './JobTypeRedirect';
import JobList from '../../components/JobList';
import { JOB_TYPE_URL_SEGMENTS } from '../../constants';

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

  function TypeRedirect({ view }) {
    const { id } = useParams();
    const { path } = useRouteMatch();
    return <JobTypeRedirect id={id} path={path} view={view} />;
  }

  return (
    <>
      <Breadcrumbs breadcrumbConfig={breadcrumbConfig} />
      <Switch>
        <Route exact path={match.path}>
          <PageSection>
            <JobList showTypeColumn />
          </PageSection>
        </Route>
        <Route path={`${match.path}/:id/details`}>
          <TypeRedirect view="details" />
        </Route>
        <Route path={`${match.path}/:id/output`}>
          <TypeRedirect view="output" />
        </Route>
        <Route path={`${match.path}/:type/:id`}>
          <Job
            history={history}
            location={location}
            setBreadcrumb={buildBreadcrumbConfig}
          />
        </Route>
        <Route path={`${match.path}/:id`}>
          <TypeRedirect />
        </Route>
      </Switch>
    </>
  );
}

export { Jobs as _Jobs };
export default withI18n()(Jobs);
