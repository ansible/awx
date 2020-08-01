import React, { Component } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Switch, Route, withRouter, Redirect, Link } from 'react-router-dom';
import { CaretLeftIcon } from '@patternfly/react-icons';
import { Card, PageSection } from '@patternfly/react-core';
import RoutedTabs from '../../components/RoutedTabs';
import ContentError from '../../components/ContentError';
import NotificationList from '../../components/NotificationList/NotificationList';
import { ResourceAccessList } from '../../components/ResourceAccessList';
import OrganizationDetail from './OrganizationDetail';
import OrganizationEdit from './OrganizationEdit';
import OrganizationTeams from './OrganizationTeams';
import { OrganizationsAPI } from '../../api';

class Organization extends Component {
  constructor(props) {
    super(props);

    this.state = {
      organization: null,
      hasContentLoading: true,
      contentError: null,
      isInitialized: false,
      isNotifAdmin: false,
      isAuditorOfThisOrg: false,
      isAdminOfThisOrg: false,
    };
    this.loadOrganization = this.loadOrganization.bind(this);
    this.loadOrganizationAndRoles = this.loadOrganizationAndRoles.bind(this);
  }

  async componentDidMount() {
    await this.loadOrganizationAndRoles();
    this.setState({ isInitialized: true });
  }

  async componentDidUpdate(prevProps) {
    const { location, match } = this.props;
    const url = `/organizations/${match.params.id}/`;

    if (
      prevProps.location.pathname.startsWith(url) &&
      prevProps.location !== location &&
      location.pathname === `${url}details`
    ) {
      await this.loadOrganization();
    }
  }

  async loadOrganizationAndRoles() {
    const { match, setBreadcrumb } = this.props;
    const id = parseInt(match.params.id, 10);

    this.setState({ contentError: null, hasContentLoading: true });
    try {
      const [{ data }, notifAdminRes, auditorRes, adminRes] = await Promise.all(
        [
          OrganizationsAPI.readDetail(id),
          OrganizationsAPI.read({
            page_size: 1,
            role_level: 'notification_admin_role',
          }),
          OrganizationsAPI.read({ id, role_level: 'auditor_role' }),
          OrganizationsAPI.read({ id, role_level: 'admin_role' }),
        ]
      );
      setBreadcrumb(data);
      this.setState({
        organization: data,
        isNotifAdmin: notifAdminRes.data.results.length > 0,
        isAuditorOfThisOrg: auditorRes.data.results.length > 0,
        isAdminOfThisOrg: adminRes.data.results.length > 0,
      });
    } catch (err) {
      this.setState({ contentError: err });
    } finally {
      this.setState({ hasContentLoading: false });
    }
  }

  async loadOrganization() {
    const { match, setBreadcrumb } = this.props;
    const id = parseInt(match.params.id, 10);

    this.setState({ contentError: null, hasContentLoading: true });
    try {
      const { data } = await OrganizationsAPI.readDetail(id);
      setBreadcrumb(data);
      this.setState({ organization: data });
    } catch (err) {
      this.setState({ contentError: err });
    } finally {
      this.setState({ hasContentLoading: false });
    }
  }

  render() {
    const { location, match, me, i18n } = this.props;

    const {
      organization,
      contentError,
      hasContentLoading,
      isInitialized,
      isNotifAdmin,
      isAuditorOfThisOrg,
      isAdminOfThisOrg,
    } = this.state;

    const canSeeNotificationsTab =
      me.is_system_auditor || isNotifAdmin || isAuditorOfThisOrg;
    const canToggleNotifications =
      isNotifAdmin &&
      (me.is_system_auditor || isAuditorOfThisOrg || isAdminOfThisOrg);

    const tabsArray = [
      {
        name: (
          <>
            <CaretLeftIcon />
            {i18n._(t`Back to Organizations`)}
          </>
        ),
        link: `/organizations`,
        id: 99,
      },
      { name: i18n._(t`Details`), link: `${match.url}/details`, id: 0 },
      { name: i18n._(t`Access`), link: `${match.url}/access`, id: 1 },
      { name: i18n._(t`Teams`), link: `${match.url}/teams`, id: 2 },
    ];

    if (canSeeNotificationsTab) {
      tabsArray.push({
        name: i18n._(t`Notifications`),
        link: `${match.url}/notifications`,
        id: 3,
      });
    }

    let showCardHeader = true;

    if (!isInitialized || location.pathname.endsWith('edit')) {
      showCardHeader = false;
    }

    if (!hasContentLoading && contentError) {
      return (
        <PageSection>
          <Card>
            <ContentError error={contentError}>
              {contentError.response.status === 404 && (
                <span>
                  {i18n._(t`Organization not found.`)}{' '}
                  <Link to="/organizations">
                    {i18n._(t`View all Organizations.`)}
                  </Link>
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
          {showCardHeader && <RoutedTabs tabsArray={tabsArray} />}
          <Switch>
            <Redirect
              from="/organizations/:id"
              to="/organizations/:id/details"
              exact
            />
            {organization && (
              <Route path="/organizations/:id/edit">
                <OrganizationEdit organization={organization} />
              </Route>
            )}
            {organization && (
              <Route path="/organizations/:id/details">
                <OrganizationDetail organization={organization} />
              </Route>
            )}
            {organization && (
              <Route path="/organizations/:id/access">
                <ResourceAccessList
                  resource={organization}
                  apiModel={OrganizationsAPI}
                />
              </Route>
            )}
            <Route path="/organizations/:id/teams">
              <OrganizationTeams id={Number(match.params.id)} />
            </Route>
            {canSeeNotificationsTab && (
              <Route path="/organizations/:id/notifications">
                <NotificationList
                  id={Number(match.params.id)}
                  canToggleNotifications={canToggleNotifications}
                  apiModel={OrganizationsAPI}
                />
              </Route>
            )}
            <Route key="not-found" path="*">
              {!hasContentLoading && (
                <ContentError isNotFound>
                  {match.params.id && (
                    <Link to={`/organizations/${match.params.id}/details`}>
                      {i18n._(t`View Organization Details`)}
                    </Link>
                  )}
                </ContentError>
              )}
            </Route>
            ,
          </Switch>
        </Card>
      </PageSection>
    );
  }
}

export default withI18n()(withRouter(Organization));
export { Organization as _Organization };
