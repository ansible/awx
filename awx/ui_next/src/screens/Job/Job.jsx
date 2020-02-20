import React, { Component } from 'react';
import { Route, withRouter, Switch, Redirect, Link } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Card, CardActions, PageSection } from '@patternfly/react-core';
import { JobsAPI } from '@api';
import { TabbedCardHeader } from '@components/Card';
import ContentError from '@components/ContentError';
import CardCloseButton from '@components/CardCloseButton';
import RoutedTabs from '@components/RoutedTabs';

import JobDetail from './JobDetail';
import JobOutput from './JobOutput';
import WorkflowDetail from './WorkflowDetail';
import { WorkflowOutput } from './WorkflowOutput';
import { JOB_TYPE_URL_SEGMENTS } from '@constants';

class Job extends Component {
  constructor(props) {
    super(props);

    this.state = {
      job: null,
      contentError: null,
      hasContentLoading: true,
      isInitialized: false,
    };

    this.loadJob = this.loadJob.bind(this);
  }

  async componentDidMount() {
    await this.loadJob();
    this.setState({ isInitialized: true });
  }

  async componentDidUpdate(prevProps) {
    const { location } = this.props;
    if (location !== prevProps.location) {
      await this.loadJob();
    }
  }

  async loadJob() {
    const { match, setBreadcrumb } = this.props;
    const id = parseInt(match.params.id, 10);

    this.setState({ contentError: null, hasContentLoading: true });
    try {
      const { data } = await JobsAPI.readDetail(id, match.params.type);
      setBreadcrumb(data);
      this.setState({ job: data });
    } catch (err) {
      this.setState({ contentError: err });
    } finally {
      this.setState({ hasContentLoading: false });
    }
  }

  render() {
    const { match, i18n, lookup } = this.props;

    const { job, contentError, hasContentLoading, isInitialized } = this.state;
    let jobType;
    if (job) {
      jobType = JOB_TYPE_URL_SEGMENTS[job.type];
    }

    const tabsArray = [
      { name: i18n._(t`Details`), link: `${match.url}/details`, id: 0 },
      { name: i18n._(t`Output`), link: `${match.url}/output`, id: 1 },
    ];

    let cardHeader = (
      <TabbedCardHeader>
        <RoutedTabs tabsArray={tabsArray} />
        <CardActions>
          <CardCloseButton linkTo="/jobs" />
        </CardActions>
      </TabbedCardHeader>
    );

    if (!isInitialized) {
      cardHeader = null;
    }

    if (!hasContentLoading && contentError) {
      return (
        <PageSection>
          <Card>
            <ContentError error={contentError}>
              {contentError.response.status === 404 && (
                <span>
                  {i18n._(`The page you requested could not be found.`)}{' '}
                  <Link to="/jobs">{i18n._(`View all Jobs.`)}</Link>
                </span>
              )}
            </ContentError>
          </Card>
        </PageSection>
      );
    }

    if (lookup && job) {
      return (
        <Switch>
          <Redirect from="jobs/:id" to={`/jobs/${jobType}/:id/output`} />
          <Redirect
            from="jobs/:id/details"
            to={`/jobs/${jobType}/:id/details`}
          />
          <Redirect from="jobs/:id/output" to={`/jobs/${jobType}/:id/output`} />
        </Switch>
      );
    }

    return (
      <PageSection>
        <Card>
          {cardHeader}
          <Switch>
            <Redirect
              from="/jobs/:type/:id"
              to="/jobs/:type/:id/output"
              exact
            />
            <Route
              key="workflow-details"
              path="/jobs/workflow/:id/details"
              render={() =>
                job &&
                job.type === 'workflow_job' && <WorkflowDetail job={job} />
              }
            />
            <Route
              key="workflow-output"
              path="/jobs/workflow/:id/output"
              render={() =>
                job &&
                job.type === 'workflow_job' && <WorkflowOutput job={job} />
              }
            />
            {job &&
              job.type !== 'workflow_job' && [
                <Route
                  key="details"
                  path="/jobs/:type/:id/details"
                  render={() => (
                    <JobDetail type={match.params.type} job={job} />
                  )}
                />,
                <Route
                  key="output"
                  path="/jobs/:type/:id/output"
                  render={() => (
                    <JobOutput type={match.params.type} job={job} />
                  )}
                />,
                <Route
                  key="not-found"
                  path="*"
                  render={() =>
                    !hasContentLoading && (
                      <ContentError isNotFound>
                        <Link
                          to={`/jobs/${match.params.type}/${match.params.id}/details`}
                        >
                          {i18n._(`View Job Details`)}
                        </Link>
                      </ContentError>
                    )
                  }
                />,
              ]}
          </Switch>
        </Card>
      </PageSection>
    );
  }
}

export default withI18n()(withRouter(Job));
export { Job as _Job };
