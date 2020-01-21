import React, { Component } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Switch, Route, withRouter, Redirect, Link } from 'react-router-dom';
import { Card } from '@patternfly/react-core';
import { CaretLeftIcon } from '@patternfly/react-icons';

import { TabbedCardHeader } from '@components/Card';
import CardCloseButton from '@components/CardCloseButton';
import RoutedTabs from '@components/RoutedTabs';
import ContentError from '@components/ContentError';
import ContentLoading from '@components/ContentLoading';
import HostFacts from './HostFacts';
import HostDetail from './HostDetail';

import HostEdit from './HostEdit';
import HostGroups from './HostGroups';
import HostCompletedJobs from './HostCompletedJobs';
import { HostsAPI } from '@api';

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
    const { match, setBreadcrumb, history, inventory } = this.props;

    this.setState({ contentError: null, hasContentLoading: true });
    try {
      const { data } = await HostsAPI.readDetail(
        match.params.hostId || match.params.id
      );
      this.setState({ host: data });

      if (history.location.pathname.startsWith('/hosts')) {
        setBreadcrumb(data);
      } else {
        setBreadcrumb(inventory, data);
      }
    } catch (err) {
      this.setState({ contentError: err });
    } finally {
      this.setState({ hasContentLoading: false });
    }
  }

  render() {
    const { location, match, history, i18n } = this.props;
    const { host, hasContentLoading, isInitialized, contentError } = this.state;

    const tabsArray = [
      {
        name: i18n._(t`Details`),
        link: `${match.url}/details`,
        id: 0,
      },
      {
        name: i18n._(t`Facts`),
        link: `${match.url}/facts`,
        id: 1,
      },
      {
        name: i18n._(t`Groups`),
        link: `${match.url}/groups`,
        id: 2,
      },
      {
        name: i18n._(t`Completed Jobs`),
        link: `${match.url}/completed_jobs`,
        id: 3,
      },
    ];

    if (!history.location.pathname.startsWith('/hosts')) {
      tabsArray.unshift({
        name: (
          <>
            <CaretLeftIcon />
            {i18n._(t`Back to Hosts`)}
          </>
        ),
        link: `/inventories/inventory/${match.params.id}/hosts`,
        id: 99,
      });
    }

    let cardHeader = (
      <TabbedCardHeader>
        <RoutedTabs tabsArray={tabsArray} />
        <CardCloseButton linkTo="/hosts" />
      </TabbedCardHeader>
    );

    if (!isInitialized) {
      cardHeader = null;
    }

    if (location.pathname.endsWith('edit')) {
      cardHeader = null;
    }

    if (hasContentLoading) {
      return <ContentLoading />;
    }

    if (!hasContentLoading && contentError) {
      return (
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
      );
    }

    const redirect = location.pathname.startsWith('/hosts') ? (
      <Redirect from="/hosts/:id" to="/hosts/:id/details" exact />
    ) : (
      <Redirect
        from="/inventories/inventory/:id/hosts/:hostId"
        to="/inventories/inventory/:id/hosts/:hostId/details"
        exact
      />
    );

    return (
      <Card className="awx-c-card">
        {cardHeader}
        <Switch>
          {redirect}
          {host && (
            <Route
              path={[
                '/hosts/:id/details',
                '/inventories/inventory/:id/hosts/:hostId/details',
              ]}
              render={() => (
                <HostDetail
                  host={host}
                  onUpdateHost={newHost => this.setState({ host: newHost })}
                />
              )}
            />
          )}
          ))
          {host && (
            <Route
              path={[
                '/hosts/:id/edit',
                '/inventories/inventory/:id/hosts/:hostId/edit',
              ]}
              render={() => <HostEdit host={host} />}
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
    );
  }
}

export default withI18n()(withRouter(Host));
export { Host as _Host };
