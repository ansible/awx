import React, { Component } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Switch, Route, withRouter, Redirect } from 'react-router-dom';
import { Card, CardHeader, PageSection } from '@patternfly/react-core';
import { withNetwork } from '../../../../contexts/Network';
import NotifyAndRedirect from '../../../../components/NotifyAndRedirect';
import CardCloseButton from '../../../../components/CardCloseButton';
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
      isNotifAdmin: false,
      isAuditorOfThisOrg: false,
      isAdminOfThisOrg: false
    };

    this.fetchOrganization = this.fetchOrganization.bind(this);
    this.fetchOrganizationAndRoles = this.fetchOrganizationAndRoles.bind(this);
  }

  componentDidMount () {
    this.fetchOrganizationAndRoles();
  }

  async componentDidUpdate (prevProps) {
    const { location } = this.props;
    if (location !== prevProps.location) {
      await this.fetchOrganization();
    }
  }

  async fetchOrganizationAndRoles () {
    const {
      match,
      setBreadcrumb,
      api,
      handleHttpError
    } = this.props;

    try {
      const [{ data }, notifAdminRest, auditorRes, adminRes] = await Promise.all([
        api.getOrganizationDetails(parseInt(match.params.id, 10)),
        api.getOrganizations({
          role_level: 'notification_admin_role',
          page_size: 1
        }),
        api.getOrganizations({
          role_level: 'auditor_role',
          id: parseInt(match.params.id, 10)
        }),
        api.getOrganizations({
          role_level: 'admin_role',
          id: parseInt(match.params.id, 10)
        })
      ]);
      setBreadcrumb(data);
      this.setState({
        organization: data,
        loading: false,
        isNotifAdmin: notifAdminRest.data.results.length > 0,
        isAuditorOfThisOrg: auditorRes.data.results.length > 0,
        isAdminOfThisOrg: adminRes.data.results.length > 0
      });
    } catch (error) {
      handleHttpError(error) || this.setState({ error: true, loading: false });
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
      me,
      history,
      i18n
    } = this.props;

    const {
      organization,
      error,
      loading,
      isNotifAdmin,
      isAuditorOfThisOrg,
      isAdminOfThisOrg
    } = this.state;

    const tabsStyle = {
      paddingTop: '0px',
      paddingLeft: '0px',
      paddingRight: '0px',
    };

    const canSeeNotificationsTab = me.is_system_auditor || isNotifAdmin || isAuditorOfThisOrg;
    const canToggleNotifications = isNotifAdmin && (
      me.is_system_auditor
      || isAuditorOfThisOrg
      || isAdminOfThisOrg
    );

    const tabsArray = [
      { name: i18n._(t`Details`), link: `${match.url}/details`, id: 0 },
      { name: i18n._(t`Access`), link: `${match.url}/access`, id: 1 },
      { name: i18n._(t`Teams`), link: `${match.url}/teams`, id: 2 }
    ];

    if (canSeeNotificationsTab) {
      tabsArray.push({
        name: i18n._(t`Notifications`),
        link: `${match.url}/notifications`,
        id: 3
      });
    }

    let cardHeader = (
      loading ? ''
        : (
          <CardHeader
            style={tabsStyle}
          >
            <div className="awx-orgTabs-container">
              <RoutedTabs
                match={match}
                history={history}
                labeltext={i18n._(t`Organization detail tabs`)}
                tabsArray={tabsArray}
              />
              <CardCloseButton linkTo="/organizations" />
              <div
                className="awx-orgTabs__bottom-border"
              />
            </div>
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
            {organization && (
              <Route
                path="/organizations/:id/access"
                render={() => (
                  <OrganizationAccess
                    organization={organization}
                  />
                )}
              />
            )}
            <Route
              path="/organizations/:id/teams"
              render={() => (
                <OrganizationTeams id={Number(match.params.id)} />
              )}
            />
            {canSeeNotificationsTab && (
              <Route
                path="/organizations/:id/notifications"
                render={() => (
                  <OrganizationNotifications
                    id={Number(match.params.id)}
                    canToggleNotifications={canToggleNotifications}
                  />
                )}
              />
            )}
            {organization && (
              <NotifyAndRedirect
                to={`/organizations/${match.params.id}/details`}
              />
            )}
          </Switch>
          {error ? 'error!' : ''}
          {loading ? 'loading...' : ''}
        </Card>
      </PageSection>
    );
  }
}
export default withI18n()(withNetwork(withRouter(Organization)));
export { Organization as _Organization };
