import React, { useEffect, useCallback } from 'react';
import {
  Route,
  withRouter,
  Switch,
  Redirect,
  Link,
  useParams,
  useRouteMatch,
} from 'react-router-dom';

import { t } from '@lingui/macro';
import { CaretLeftIcon } from '@patternfly/react-icons';
import { Card, PageSection } from '@patternfly/react-core';
import ContentError from '../../components/ContentError';
import ContentLoading from '../../components/ContentLoading';
import RoutedTabs from '../../components/RoutedTabs';
import useRequest from '../../util/useRequest';
import { getJobModel } from '../../util/jobs';
import JobDetail from './JobDetail';
import JobOutput from './JobOutput';
import { WorkflowOutput } from './WorkflowOutput';
import useWsJob from './useWsJob';

// maps the displayed url segments to actual api types
export const JOB_URL_SEGMENT_MAP = {
  playbook: 'job',
  project: 'project_update',
  management: 'system_job',
  inventory: 'inventory_update',
  command: 'ad_hoc_command',
  workflow: 'workflow_job',
};

function Job({ setBreadcrumb }) {
  const { id, typeSegment } = useParams();
  const match = useRouteMatch();

  const type = JOB_URL_SEGMENT_MAP[typeSegment];

  const {
    isLoading,
    error,
    request: fetchJob,
    result: { jobDetail, eventRelatedSearchableKeys, eventSearchableKeys },
  } = useRequest(
    useCallback(async () => {
      let eventOptions = {};
      const { data: jobDetailData } = await getJobModel(type).readDetail(id);
      if (type !== 'workflow_job') {
        const { data: jobEventOptions } = await getJobModel(
          type
        ).readEventOptions(id);
        eventOptions = jobEventOptions;
      }
      if (
        jobDetailData?.summary_fields?.credentials?.find(
          cred => cred.kind === 'vault'
        )
      ) {
        const {
          data: { results },
        } = await getJobModel(type).readCredentials(jobDetailData.id);

        jobDetailData.summary_fields.credentials = results;
      }
      setBreadcrumb(jobDetailData);

      return {
        jobDetail: jobDetailData,
        eventRelatedSearchableKeys: (
          eventOptions?.related_search_fields || []
        ).map(val => val.slice(0, -8)),
        eventSearchableKeys: Object.keys(
          eventOptions?.actions?.GET || {}
        ).filter(key => eventOptions?.actions?.GET[key].filterable),
      };
    }, [id, type, setBreadcrumb]),
    {
      jobDetail: null,
      eventRelatedSearchableKeys: [],
      eventSearchableKeys: [],
    }
  );

  useEffect(() => {
    fetchJob();
  }, [fetchJob]);

  const job = useWsJob(jobDetail);

  const tabsArray = [
    {
      name: (
        <>
          <CaretLeftIcon />
          {t`Back to Jobs`}
        </>
      ),
      link: `/jobs`,
      id: 99,
    },
    { name: t`Details`, link: `${match.url}/details`, id: 0 },
    { name: t`Output`, link: `${match.url}/output`, id: 1 },
  ];

  if (isLoading) {
    return (
      <PageSection>
        <Card>
          <ContentLoading />
        </Card>
      </PageSection>
    );
  }

  if (error) {
    return (
      <PageSection>
        <Card>
          <ContentError error={error}>
            {error.response.status === 404 && (
              <span>
                {t`The page you requested could not be found.`}{' '}
                <Link to="/jobs">{t`View all Jobs.`}</Link>
              </span>
            )}
          </ContentError>
        </Card>
      </PageSection>
    );
  }

  return (
    <PageSection>
      <Card>
        <RoutedTabs tabsArray={tabsArray} />
        <Switch>
          <Redirect
            from="/jobs/:typeSegment/:id"
            to="/jobs/:typeSegment/:id/output"
            exact
          />
          {job && [
            <Route
              key={job.type === 'workflow_job' ? 'workflow-details' : 'details'}
              path="/jobs/:typeSegment/:id/details"
            >
              <JobDetail job={job} />
            </Route>,
            <Route key="output" path="/jobs/:typeSegment/:id/output">
              {job.type === 'workflow_job' ? (
                <WorkflowOutput job={job} />
              ) : (
                <JobOutput
                  job={job}
                  eventRelatedSearchableKeys={eventRelatedSearchableKeys}
                  eventSearchableKeys={eventSearchableKeys}
                />
              )}
            </Route>,
            <Route key="not-found" path="*">
              <ContentError isNotFound>
                <Link to={`/jobs/${typeSegment}/${id}/details`}>
                  {t`View Job Details`}
                </Link>
              </ContentError>
            </Route>,
          ]}
        </Switch>
      </Card>
    </PageSection>
  );
}

export default withRouter(Job);
export { Job as _Job };
