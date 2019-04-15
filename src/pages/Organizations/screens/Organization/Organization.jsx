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
  Tab,
  Tabs
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

class Organization extends Component {
  constructor (props) {
    super(props);

    this.state = {
      organization: null,
      error: false,
      loading: true,
      tabElements: [
        { name: i18nMark('Details'), link: `${props.match.url}/details`, id: 0 },
        { name: i18nMark('Access'), link: `${props.match.url}/access`, id: 1 },
        { name: i18nMark('Teams'), link: `${props.match.url}/teams`, id: 2 },
        { name: i18nMark('Notifications'), link: `${props.match.url}/notifications`, id: 3 },
      ],
    };

    this.fetchOrganization = this.fetchOrganization.bind(this);
    this.handleTabSelect = this.handleTabSelect.bind(this);
    this.checkLocation = this.checkLocation.bind(this);
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
      this.setState({ error: true });
    } finally {
      this.setState({ loading: false });
      this.checkLocation();
    }
  }

  checkLocation () {
    const { location } = this.props;
    const { tabElements } = this.state;
    const activeTab = tabElements.filter(tabElement => tabElement.link === location.pathname);
    this.setState({ activeTabKey: activeTab[0].id });
  }

  handleTabSelect (event, eventKey) {
    const { history } = this.props;
    const { tabElements } = this.state;

    const tab = tabElements.find(tabElement => tabElement.id === eventKey);
    history.push(tab.link);
    const activeTab = tabElements.filter(selectedTab => selectedTab.link === tab.link)
      .map(selectedTab => selectedTab.id);
    this.setState({ activeTabKey: activeTab[0] });
  }

  render () {
    const {
      location,
      match,
      history
    } = this.props;
    const {
      activeTabKey,
      organization,
      error,
      loading,
      tabElements
    } = this.state;

    let cardHeader = (
      <CardHeader>
        <I18n>
          {({ i18n }) => (
            <>
              <Tabs
                labeltext={i18n._(t`Organization detail tabs`)}
                activeKey={activeTabKey}
                onSelect={(event, eventKey) => {
                  this.handleTabSelect(event, eventKey);
                }}
              >
                {tabElements.map(tabElement => (
                  <Tab
                    className={`${tabElement.name}`}
                    aria-label={`${tabElement.name}`}
                    eventKey={tabElement.id}
                    key={tabElement.id}
                    link={tabElement.link}
                    title={tabElement.name}
                  />
                ))}
              </Tabs>
              <Link
                aria-label="Close"
                title="Close"
                to="/organizations"
              >
                <TimesIcon className="OrgsTab-closeButton" />
              </Link>
            </>
          )}
        </I18n>
      </CardHeader>
    );

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
                <OrganizationAccess
                  match={match}
                  location={location}
                  history={history}
                />
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
