import React, { Component } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Switch, Route, withRouter, Redirect, Link } from 'react-router-dom';
import { Card, PageSection } from '@patternfly/react-core';
import { TabbedCardHeader } from '@components/Card';
import CardCloseButton from '@components/CardCloseButton';
import RoutedTabs from '@components/RoutedTabs';
import ContentError from '@components/ContentError';
import HostFacts from './HostFacts';
import HostDetail from './HostDetail';
import AlertModal from '@components/AlertModal';
import ErrorDetail from '@components/ErrorDetail';

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
      toggleLoading: false,
      toggleError: null,
      deletionError: false,
      isDeleteModalOpen: false,
    };
    this.loadHost = this.loadHost.bind(this);
    this.handleHostToggle = this.handleHostToggle.bind(this);
    this.handleToggleError = this.handleToggleError.bind(this);
    this.handleHostDelete = this.handleHostDelete.bind(this);
    this.toggleDeleteModal = this.toggleDeleteModal.bind(this);
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

  toggleDeleteModal() {
    const { isDeleteModalOpen } = this.state;
    this.setState({ isDeleteModalOpen: !isDeleteModalOpen });
  }

  async handleHostToggle() {
    const { host } = this.state;
    this.setState({ toggleLoading: true });
    try {
      const { data } = await HostsAPI.update(host.id, {
        enabled: !host.enabled,
      });
      this.setState({ host: data });
    } catch (err) {
      this.setState({ toggleError: err });
    } finally {
      this.setState({ toggleLoading: null });
    }
  }

  async handleHostDelete() {
    const { host } = this.state;
    const { match, history } = this.props;

    this.setState({ hasContentLoading: true });
    try {
      await HostsAPI.destroy(host.id);
      this.setState({ hasContentLoading: false });
      history.push(`/inventories/inventory/${match.params.id}/hosts`);
    } catch (err) {
      this.setState({ deletionError: err });
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
      }
      setBreadcrumb(inventory, data);
    } catch (err) {
      this.setState({ contentError: err });
    } finally {
      this.setState({ hasContentLoading: false });
    }
  }

  handleToggleError() {
    this.setState({ toggleError: false });
  }

  render() {
    const { location, match, history, i18n } = this.props;
    const {
      deletionError,
      host,
      isDeleteModalOpen,
      toggleError,
      hasContentLoading,
      toggleLoading,
      isInitialized,
      contentError,
    } = this.state;
    const tabsArray = [
      {
        name: i18n._(t`Return to Hosts`),
        link: `/inventories/inventory/${match.params.id}/hosts`,
        id: 99,
        isNestedTab: !history.location.pathname.startsWith('/hosts'),
      },
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

    let cardHeader = (
      <TabbedCardHeader>
        <RoutedTabs
          match={match}
          history={history}
          labeltext={i18n._(t`Host detail tabs`)}
          tabsArray={tabsArray}
        />
        <CardCloseButton linkTo="/hosts" />
      </TabbedCardHeader>
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
      <>
        <PageSection
          css={`
            ${location.pathname.startsWith('/inventories')
              ? 'padding: 0'
              : 'null'}
          `}
        >
          <Card className="awx-c-card">
            {cardHeader}
            <Switch>
              <Redirect from="/hosts/:id" to="/hosts/:id/details" exact />
              {host && (
                <Route
                  path={[
                    '/hosts/:id/edit',
                    '/inventories/inventory/:id/hosts/:hostId/edit',
                  ]}
                  render={() => <HostEdit match={match} host={host} />}
                />
              )}
              {host && (
                <Route
                  path={[
                    '/hosts/:id/details',
                    '/inventories/inventory/:id/hosts/:hostId/details',
                  ]}
                  render={() => (
                    <HostDetail
                      match={match}
                      host={host}
                      history={history}
                      onToggleDeleteModal={this.toggleDeleteModal}
                      isDeleteModalOpen={isDeleteModalOpen}
                      onHandleHostToggle={this.handleHostToggle}
                      toggleError={toggleError}
                      toggleLoading={toggleLoading}
                      onToggleError={this.handleToggleError}
                      onHostDelete={this.handleHostDelete}
                    />
                  )}
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
        {deletionError && (
          <AlertModal
            isOpen={deletionError}
            variant="danger"
            title={i18n._(t`Error!`)}
            onClose={() => this.setState({ deletionError: false })}
          >
            {i18n._(t`Failed to delete ${host.name}.`)}
            <ErrorDetail error={deletionError} />
          </AlertModal>
        )}
      </>
    );
  }
}

export default withI18n()(withRouter(Host));
export { Host as _Host };
