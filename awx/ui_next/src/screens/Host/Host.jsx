import React, { Component } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Switch, Route, withRouter, Redirect, Link } from 'react-router-dom';
import {
  Card,
  CardHeader as PFCardHeader,
  PageSection,
} from '@patternfly/react-core';
import styled from 'styled-components';
import CardCloseButton from '@components/CardCloseButton';
import RoutedTabs from '@components/RoutedTabs';
import ContentError from '@components/ContentError';
import HostFacts from './HostFacts';
import HostDetail from './HostDetail';
import HostEdit from './HostEdit';
import HostGroups from './HostGroups';
import HostCompletedJobs from './HostCompletedJobs';
import { HostsAPI } from '@api';

const CardHeader = styled(PFCardHeader)`
  --pf-c-card--first-child--PaddingTop: 0;
  --pf-c-card--child--PaddingLeft: 0;
  --pf-c-card--child--PaddingRight: 0;
  position: relative;
`;

class Host extends Component {
  constructor(props) {
    super(props);

    this.state = {
      host: null,
      hasContentLoading: true,
      contentError: null,
      isInitialized: false,
    };
    this.loadHost = this.loadHost.bind(this);
  }

  async componentDidMount() {
    await this.loadHost();
    this.setState({ isInitialized: true });
  }

  async componentDidUpdate(prevProps) {
    const { location, match } = this.props;
    const url = `/hosts/${match.params.id}/`;

    if (
      prevProps.location.pathname.startsWith(url) &&
      prevProps.location !== location &&
      location.pathname === `${url}details`
    ) {
      await this.loadHost();
    }
  }

  async loadHost() {
    const { match, setBreadcrumb } = this.props;
    const id = parseInt(match.params.id, 10);

    this.setState({ contentError: null, hasContentLoading: true });
    try {
      const { data } = await HostsAPI.readDetail(id);
      setBreadcrumb(data);
      this.setState({ host: data });
    } catch (err) {
      this.setState({ contentError: err });
    } finally {
      this.setState({ hasContentLoading: false });
    }
  }

  render() {
    const { location, match, history, i18n } = this.props;

    const { host, contentError, hasContentLoading, isInitialized } = this.state;

    const tabsArray = [
      { name: i18n._(t`Details`), link: `${match.url}/details`, id: 0 },
      { name: i18n._(t`Facts`), link: `${match.url}/facts`, id: 1 },
      { name: i18n._(t`Groups`), link: `${match.url}/groups`, id: 2 },
      {
        name: i18n._(t`Completed Jobs`),
        link: `${match.url}/completed_jobs`,
        id: 3,
      },
    ];

    let cardHeader = (
      <CardHeader style={{ padding: 0 }}>
        <RoutedTabs
          match={match}
          history={history}
          labeltext={i18n._(t`Host detail tabs`)}
          tabsArray={tabsArray}
        />
        <CardCloseButton linkTo="/hosts" />
      </CardHeader>
    );

    if (!isInitialized) {
      cardHeader = null;
    }

    if (!match) {
      cardHeader = null;
    }

    if (location.pathname.endsWith('edit')) {
      cardHeader = null;
    }

    if (!hasContentLoading && contentError) {
      return (
        <PageSection>
          <Card className="awx-c-card">
            <ContentError error={contentError}>
              {contentError.response.status === 404 && (
                <span>
                  {i18n._(`Host not found.`)}{' '}
                  <Link to="/hosts">{i18n._(`View all Hosts.`)}</Link>
                </span>
              )}
            </ContentError>
          </Card>
        </PageSection>
      );
    }

    return (
      <PageSection>
        <Card className="awx-c-card">
          {cardHeader}
          <Switch>
            <Redirect from="/hosts/:id" to="/hosts/:id/details" exact />
            {host && (
              <Route
                path="/hosts/:id/edit"
                render={() => <HostEdit match={match} host={host} />}
              />
            )}
            {host && (
              <Route
                path="/hosts/:id/details"
                render={() => <HostDetail match={match} host={host} />}
              />
            )}
            {host && (
              <Route
                path="/hosts/:id/facts"
                render={() => <HostFacts host={host} />}
              />
            )}
            {host && (
              <Route
                path="/hosts/:id/groups"
                render={() => <HostGroups host={host} />}
              />
            )}
            {host && (
              <Route
                path="/hosts/:id/completed_jobs"
                render={() => <HostCompletedJobs host={host} />}
              />
            )}
            <Route
              key="not-found"
              path="*"
              render={() =>
                !hasContentLoading && (
                  <ContentError isNotFound>
                    {match.params.id && (
                      <Link to={`/hosts/${match.params.id}/details`}>
                        {i18n._(`View Host Details`)}
                      </Link>
                    )}
                  </ContentError>
                )
              }
            />
            ,
          </Switch>
        </Card>
      </PageSection>
    );
  }
}

export default withI18n()(withRouter(Host));
export { Host as _Host };
