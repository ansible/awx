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
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { CaretLeftIcon } from '@patternfly/react-icons';
import { Card, PageSection } from '@patternfly/react-core';
import { JobsAPI } from '../../api';
import ContentError from '../../components/ContentError';
import ContentLoading from '../../components/ContentLoading';
import RoutedTabs from '../../components/RoutedTabs';
import useRequest from '../../util/useRequest';
import JobDetail from './JobDetail';
import JobOutput from './JobOutput';
import { WorkflowOutput } from './WorkflowOutput';
import useWsJob from './useWsJob';

function Job({ i18n, setBreadcrumb }) {
  const { id, type } = useParams();
  const match = useRouteMatch();

  const { isLoading, error, request: fetchJob, result } = useRequest(
    useCallback(async () => {
      const { data } = await JobsAPI.readDetail(id, type);
      if (
        data?.summary_fields?.credentials?.find(cred => cred.kind === 'vault')
      ) {
        const {
          data: { results },
        } = await JobsAPI.readCredentials(data.id, type);

        data.summary_fields.credentials = results;
      }
      setBreadcrumb(data);
      return data;
    }, [id, type, setBreadcrumb])
  );

  useEffect(() => {
    fetchJob();
  }, [fetchJob]);

  const job = useWsJob(result);

  const tabsArray = [
    {
      name: (
        <>
          <CaretLeftIcon />
          {i18n._(t`Back to Jobs`)}
        </>
      ),
      link: `/jobs`,
      id: 99,
    },
    { name: i18n._(t`Details`), link: `${match.url}/details`, id: 0 },
    { name: i18n._(t`Output`), link: `${match.url}/output`, id: 1 },
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
                {i18n._(t`The page you requested could not be found.`)}{' '}
                <Link to="/jobs">{i18n._(t`View all Jobs.`)}</Link>
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
          <Redirect from="/jobs/:type/:id" to="/jobs/:type/:id/output" exact />
          {job &&
            job.type === 'workflow_job' && [
              <Route key="workflow-details" path="/jobs/workflow/:id/details">
                <JobDetail type={match.params.type} job={job} />
              </Route>,
              <Route key="workflow-output" path="/jobs/workflow/:id/output">
                <WorkflowOutput job={job} />
              </Route>,
            ]}
          {job &&
            job.type !== 'workflow_job' && [
              <Route key="details" path="/jobs/:type/:id/details">
                <JobDetail type={type} job={job} />
              </Route>,
              <Route key="output" path="/jobs/:type/:id/output">
                <JobOutput type={type} job={job} />
              </Route>,
              <Route key="not-found" path="*">
                <ContentError isNotFound>
                  <Link to={`/jobs/${type}/${id}/details`}>
                    {i18n._(t`View Job Details`)}
                  </Link>
                </ContentError>
              </Route>,
            ]}
        </Switch>
      </Card>
    </PageSection>
  );
}

export default withI18n()(withRouter(Job));
export { Job as _Job };
