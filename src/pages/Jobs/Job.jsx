import React, { Component } from 'react'
import { Route, withRouter, Switch, Redirect } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import styled from 'styled-components';

import { withNetwork } from '../../contexts/Network';
import { JobsAPI } from '../../api';
import { Card, CardHeader as PFCardHeader, PageSection } from '@patternfly/react-core';
import CardCloseButton from '../../components/CardCloseButton';
import RoutedTabs from '../../components/Tabs/RoutedTabs';
import JobDetail from './JobDetail';
import JobOutput from './JobOutput';

export class Job extends Component {
  constructor (props) {
    super(props);

    this.state = {
      job: null,
      error: false,
      loading: true
    }

    this.fetchJob = this.fetchJob.bind(this);
  }

  componentDidMount () {
    this.fetchJob();
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
      handleHttpError
    } = this.props;

    try {
      const { data } = await JobsAPI.readDetail(match.params.id);
      setBreadcrumb(data);
      this.setState({
        job: data,
        loading: false
      })
    } catch (error) {
      handleHttpError(error) || this.setState({ error: true, loading: false });
    }
  }

  render() {
    const {
      location,
      history,
      match,
      i18n
    } = this.props;

    const {
      job,
      error,
      loading
    } = this.state;

    const tabsArray = [
      { name: i18n._(t`Details`), link: `${match.url}/details`, id: 0 },
      { name: i18n._(t`Output`), link: `${match.url}/output`, id: 1 }
    ]

    const CardHeader = styled(PFCardHeader)`
      --pf-c-card--first-child--PaddingTop: 0;
      --pf-c-card--child--PaddingLeft: 0;
      --pf-c-card--child--PaddingRight: 0;
      position: relative;
    `;

    const cardHeader = (
      loading ? '' : (
        <CardHeader>
          <RoutedTabs
            match={match}
            history={history}
            tabsArray={tabsArray}
          />
          <CardCloseButton linkTo="/jobs" />
        </CardHeader>
      )
    );

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
                    history={history}
                    location={location}
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
                    history={history}
                    location={location}
                    job={job}
                  />
                )}
              />
            )}
          </Switch>
        </Card>
      </PageSection>
    )
  }
}

export default withI18n()(withNetwork(withRouter(Job)));
