import React, { Component } from 'react';
import { Route, withRouter, Switch, Redirect } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import styled from 'styled-components';
import { Card, CardHeader as PFCardHeader, PageSection } from '@patternfly/react-core';

import { JobsAPI } from '@api';
import ContentError from '@components/ContentError';
import CardCloseButton from '@components/CardCloseButton';
import RoutedTabs from '@components/RoutedTabs';

import JobDetail from './JobDetail';
import JobOutput from './JobOutput';

export class Job extends Component {
  constructor (props) {
    super(props);

    this.state = {
      job: null,
      contentError: false,
      contentLoading: true,
      isInitialized: false
    };

    this.fetchJob = this.fetchJob.bind(this);
  }

  async componentDidMount () {
    await this.fetchJob();
    this.setState({ isInitialized: true });
  }

  async componentDidUpdate (prevProps) {
    const { location } = this.props;
    if (location !== prevProps.location) {
      await this.fetchJob();
    }
  }

  async fetchJob () {
    const {
      match,
      setBreadcrumb,
    } = this.props;
    const id = parseInt(match.params.id, 10);

    this.setState({ contentError: false, contentLoading: true });
    try {
      const { data } = await JobsAPI.readDetail(id);
      setBreadcrumb(data);
      this.setState({ job: data });
    } catch (error) {
      this.setState({ contentError: true });
    } finally {
      this.setState({ contentLoading: false });
    }
  }

  render () {
    const {
      history,
      match,
      i18n
    } = this.props;

    const {
      job,
      contentError,
      contentLoading,
      isInitialized
    } = this.state;

    const tabsArray = [
      { name: i18n._(t`Details`), link: `${match.url}/details`, id: 0 },
      { name: i18n._(t`Output`), link: `${match.url}/output`, id: 1 }
    ];

    const CardHeader = styled(PFCardHeader)`
      --pf-c-card--first-child--PaddingTop: 0;
      --pf-c-card--child--PaddingLeft: 0;
      --pf-c-card--child--PaddingRight: 0;
      position: relative;
    `;

    let cardHeader = (
      <CardHeader>
        <RoutedTabs
          match={match}
          history={history}
          tabsArray={tabsArray}
        />
        <CardCloseButton linkTo="/jobs" />
      </CardHeader>
    );

    if (!isInitialized) {
      cardHeader = null;
    }

    if (!match) {
      cardHeader = null;
    }

    if (!contentLoading && contentError) {
      return (
        <PageSection>
          <Card className="awx-c-card">
            <ContentError />
          </Card>
        </PageSection>
      );
    }

    return (
      <PageSection>
        <Card>
          { cardHeader }
          <Switch>
            <Redirect
              from="/jobs/:id"
              to="/jobs/:id/details"
              exact
            />
            {job && (
              <Route
                path="/jobs/:id/details"
                render={() => (
                  <JobDetail
                    match={match}
                    job={job}
                  />
                )}
              />
            )}
            {job && (
              <Route
                path="/jobs/:id/output"
                render={() => (
                  <JobOutput
                    match={match}
                    job={job}
                  />
                )}
              />
            )}
          </Switch>
        </Card>
      </PageSection>
    );
  }
}

export default withI18n()(withRouter(Job));
