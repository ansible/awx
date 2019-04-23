import React, { Component } from 'react';
import { I18n, i18nMark } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  Switch,
  Route,
  withRouter,
  Redirect,
  Link
} from 'react-router-dom';
import {
  Card,
  CardHeader,
  PageSection,
} from '@patternfly/react-core';
import {
  TimesIcon
} from '@patternfly/react-icons';
import { withNetwork } from '../../../../contexts/Network';
import NotifyAndRedirect from '../../../../components/NotifyAndRedirect';
import OrganizationAccess from './OrganizationAccess';
import OrganizationDetail from './OrganizationDetail';
import OrganizationEdit from './OrganizationEdit';
import OrganizationNotifications from './OrganizationNotifications';
import OrganizationTeams from './OrganizationTeams';
import RoutedTabs from '../../../../components/Tabs/RoutedTabs';

class Organization extends Component {
  constructor (props) {
    super(props);

    this.state = {
      organization: null,
      error: false,
      loading: true,
    };

    this.fetchOrganization = this.fetchOrganization.bind(this);
  }

  componentDidMount () {
    this.fetchOrganization();
  }

  async componentDidUpdate (prevProps) {
    const { location } = this.props;
    if (location !== prevProps.location) {
      await this.fetchOrganization();
    }
  }

  async fetchOrganization () {
    const {
      match,
      setBreadcrumb,
      api,
      handleHttpError
    } = this.props;

    try {
      const { data } = await api.getOrganizationDetails(parseInt(match.params.id, 10));
      setBreadcrumb(data);
      this.setState({ organization: data, loading: false });
    } catch (error) {
      handleHttpError(error) || this.setState({ error: true, loading: false });
    }
  }

  render () {
    const {
      location,
      match,
      history
    } = this.props;

    const {
      organization,
      error,
      loading
    } = this.state;

    const tabsPaddingOverride = {
      padding: '0'
    };

    let cardHeader = (
      loading ? ''
        : (
          <CardHeader
            style={tabsPaddingOverride}
          >
            <I18n>
              {({ i18n }) => (
                <React.Fragment>
                  <RoutedTabs
                    match={match}
                    history={history}
                    labeltext={i18n._(t`Organization detail tabs`)}
                    tabsArray={[
                      { name: i18nMark('Details'), link: `${match.url}/details`, id: 0 },
                      { name: i18nMark('Access'), link: `${match.url}/access`, id: 1 },
                      { name: i18nMark('Teams'), link: `${match.url}/teams`, id: 2 },
                      { name: i18nMark('Notifications'), link: `${match.url}/notifications`, id: 3 },
                    ]}
                  />
                  <Link
                    aria-label="Close"
                    title="Close"
                    to="/organizations"
                  >
                    <TimesIcon className="OrgsTab-closeButton" />
                  </Link>
                </React.Fragment>
              )}
            </I18n>
          </CardHeader>
        ));
    if (!match) {
      cardHeader = null;
    }

    if (location.pathname.endsWith('edit')) {
      cardHeader = null;
    }

    return (
      <PageSection>
        <Card className="awx-c-card">
          { cardHeader }
          <Switch>
            <Redirect
              from="/organizations/:id"
              to="/organizations/:id/details"
              exact
            />
            {organization && (
              <Route
                path="/organizations/:id/edit"
                render={() => (
                  <OrganizationEdit
                    match={match}
                    organization={organization}
                  />
                )}
              />
            )}
            {organization && (
              <Route
                path="/organizations/:id/details"
                render={() => (
                  <OrganizationDetail
                    match={match}
                    organization={organization}
                  />
                )}
              />
            )}
            <Route
              path="/organizations/:id/access"
              render={() => (
                <OrganizationAccess />
              )}
            />
            <Route
              path="/organizations/:id/teams"
              render={() => (
                <OrganizationTeams
                  id={Number(match.params.id)}
                  match={match}
                  location={location}
                  history={history}
                />
              )}
            />
            <Route
              path="/organizations/:id/notifications"
              render={() => (
                <OrganizationNotifications
                  match={match}
                  location={location}
                  history={history}
                />
              )}
            />
            {organization && <NotifyAndRedirect to={`/organizations/${match.params.id}/details`} />}
          </Switch>
          {error ? 'error!' : ''}
          {loading ? 'loading...' : ''}
        </Card>
      </PageSection>
    );
  }
}
export default withNetwork(withRouter(Organization));
export { Organization as _Organization };
