import React, { useState, useCallback } from 'react';
import { Route, Switch, useParams, useRouteMatch } from 'react-router-dom';

import { t } from '@lingui/macro';
import { PageSection } from '@patternfly/react-core';
import ScreenHeader from 'components/ScreenHeader/ScreenHeader';
import JobList from 'components/JobList';
import PersistentFilters from 'components/PersistentFilters';
import Job from './Job';
import JobTypeRedirect from './JobTypeRedirect';
import { JOB_TYPE_URL_SEGMENTS } from '../../constants';

function TypeRedirect({ view }) {
  const { id } = useParams();
  const { path } = useRouteMatch();
  return <JobTypeRedirect id={id} path={path} view={view} />;
}

function Jobs() {
  const match = useRouteMatch();
  const [breadcrumbConfig, setBreadcrumbConfig] = useState({
    '/jobs': t`Jobs`,
  });

  const buildBreadcrumbConfig = useCallback((job) => {
    if (!job) {
      return;
    }

    const typeSegment = JOB_TYPE_URL_SEGMENTS[job.type];
    setBreadcrumbConfig({
      '/jobs': t`Jobs`,
      [`/jobs/${typeSegment}/${job.id}`]: `${job.id} - ${job.name}`,
      [`/jobs/${typeSegment}/${job.id}/output`]: t`Output`,
      [`/jobs/${typeSegment}/${job.id}/details`]: t`Details`,
    });
  }, []);

  return (
    <>
      <ScreenHeader streamType="job" breadcrumbConfig={breadcrumbConfig} />
      <Switch>
        <Route exact path={match.path}>
          <PageSection>
            <PersistentFilters pageKey="jobs">
              <JobList showTypeColumn />
            </PersistentFilters>
          </PageSection>
        </Route>
        <Route path={`${match.path}/:id/details`}>
          <TypeRedirect view="details" />
        </Route>
        <Route path={`${match.path}/:id/output`}>
          <TypeRedirect view="output" />
        </Route>
        <Route path={`${match.path}/:typeSegment/:id`}>
          <Job setBreadcrumb={buildBreadcrumbConfig} />
        </Route>
        <Route path={`${match.path}/:id`}>
          <TypeRedirect />
        </Route>
      </Switch>
    </>
  );
}

export { Jobs as _Jobs };
export default Jobs;
