import React, { useEffect, useCallback, useRef } from 'react';
import {
  Route,
  Switch,
  Redirect,
  Link,
  useParams,
  useRouteMatch,
} from 'react-router-dom';

import { t } from '@lingui/macro';
import { CaretLeftIcon } from '@patternfly/react-icons';
import { Card, PageSection } from '@patternfly/react-core';
import { InventorySourcesAPI } from 'api';
import ContentError from 'components/ContentError';
import ContentLoading from 'components/ContentLoading';
import RoutedTabs from 'components/RoutedTabs';
import { getSearchableKeys } from 'components/PaginatedTable';
import useRequest from 'hooks/useRequest';
import { getJobModel } from 'util/jobs';
import WorkflowOutputNavigation from 'components/WorkflowOutputNavigation';
import JobDetail from './JobDetail';
import JobOutput from './JobOutput';
import { WorkflowOutput } from './WorkflowOutput';
import useWsJob from './useWsJob';

// maps the displayed url segments to actual api types
export const JOB_URL_SEGMENT_MAP = {
  playbook: 'job',
  project: 'project_update',
  management: 'system_job',
  system: 'system_job',
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
    result: {
      jobDetail,
      eventRelatedSearchableKeys,
      eventSearchableKeys,
      inventorySourceChoices,
      relatedJobs,
    },
  } = useRequest(
    useCallback(async () => {
      let eventOptions = {};
      let relatedJobData = {};
      const { data: jobDetailData } = await getJobModel(type).readDetail(id);
      if (type !== 'workflow_job') {
        const { data: jobEventOptions } = await getJobModel(
          type
        ).readEventOptions(id);
        eventOptions = jobEventOptions;
      }
      if (jobDetailData.related.source_workflow_job) {
        const {
          data: { results },
        } = await getJobModel('workflow_job').readNodes(
          jobDetailData.summary_fields.source_workflow_job.id
        );
        relatedJobData = results;
      }
      if (
        jobDetailData?.summary_fields?.credentials?.find(
          (cred) => cred.kind === 'vault'
        )
      ) {
        const {
          data: { results },
        } = await getJobModel(type).readCredentials(jobDetailData.id);

        jobDetailData.summary_fields.credentials = results;
      }

      setBreadcrumb(jobDetailData);
      let choices;
      if (jobDetailData.type === 'inventory_update') {
        choices = await InventorySourcesAPI.readOptions();
      }

      return {
        inventorySourceChoices:
          choices?.data?.actions?.GET?.source?.choices || [],
        jobDetail: jobDetailData,
        relatedJobs: relatedJobData,
        eventRelatedSearchableKeys: (
          eventOptions?.related_search_fields || []
        ).map((val) => val.slice(0, -8)),
        eventSearchableKeys: getSearchableKeys(eventOptions?.actions?.GET),
      };
    }, [id, type, setBreadcrumb]),
    {
      jobDetail: null,
      inventorySourceChoices: [],
      eventRelatedSearchableKeys: [],
      eventSearchableKeys: [],
      relatedJobs: [],
    }
  );

  useEffect(() => {
    fetchJob();
  }, [fetchJob]);

  const job = useWsJob(jobDetail);
  const ref = useRef(null);
  const tabsArray = [
    {
      name: (
        <>
          <CaretLeftIcon />
          {t`Back to Jobs`}
        </>
      ),
      link: `/jobs`,
      persistentFilterKey: 'jobs',
      id: 99,
    },
    { name: t`Details`, link: `${match.url}/details`, id: 0 },
    { name: t`Output`, link: `${match.url}/output`, id: 1 },
  ];
  if (relatedJobs?.length > 0) {
    tabsArray.push({
      name: (
        <WorkflowOutputNavigation parentRef={ref} relatedJobs={relatedJobs} />
      ),
      link: undefined,
      id: 2,
      hasstyle: 'margin-left: auto',
    });
  }

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
            {error.response?.status === 404 && (
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
      <div ref={ref}>
        <Card>
          <RoutedTabs
            isWorkflow={match.url.startsWith('/jobs/workflow')}
            tabsArray={tabsArray}
          />
          <Switch>
            <Redirect from="/jobs/system/:id" to="/jobs/management/:id" exact />
            <Redirect
              from="/jobs/:typeSegment/:id"
              to="/jobs/:typeSegment/:id/output"
              exact
            />
            {job && [
              <Route
                key={
                  job.type === 'workflow_job' ? 'workflow-details' : 'details'
                }
                path="/jobs/:typeSegment/:id/details"
              >
                <JobDetail
                  job={job}
                  inventorySourceLabels={inventorySourceChoices}
                />
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
      </div>
    </PageSection>
  );
}

export default Job;
export { Job as _Job };
