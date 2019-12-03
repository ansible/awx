import React, { Component } from 'react';
import { t } from '@lingui/macro';
import { withI18n } from '@lingui/react';
import { Card, CardHeader, PageSection } from '@patternfly/react-core';
import { Switch, Route, Redirect, withRouter, Link } from 'react-router-dom';
import CardCloseButton from '@components/CardCloseButton';
import ContentError from '@components/ContentError';
import NotificationList from '@components/NotificationList';
import RoutedTabs from '@components/RoutedTabs';
import { ResourceAccessList } from '@components/ResourceAccessList';
import JobTemplateDetail from './JobTemplateDetail';
import { JobTemplatesAPI, OrganizationsAPI } from '@api';
import JobTemplateEdit from './JobTemplateEdit';

class Template extends Component {
  constructor(props) {
    super(props);

    this.state = {
      contentError: null,
      hasContentLoading: true,
      template: null,
      isNotifAdmin: false,
    };
    this.loadTemplate = this.loadTemplate.bind(this);
    this.loadTemplateAndRoles = this.loadTemplateAndRoles.bind(this);
  }

  async componentDidMount() {
    await this.loadTemplateAndRoles();
  }

  async componentDidUpdate(prevProps) {
    const { location } = this.props;
    if (location !== prevProps.location) {
      await this.loadTemplate();
    }
  }

  async loadTemplateAndRoles() {
    const { match, setBreadcrumb } = this.props;
    const id = parseInt(match.params.id, 10);

    this.setState({ contentError: null, hasContentLoading: true });
    try {
      const [{ data }, notifAdminRes] = await Promise.all([
        JobTemplatesAPI.readDetail(id),
        OrganizationsAPI.read({
          page_size: 1,
          role_level: 'notification_admin_role',
        }),
      ]);
      setBreadcrumb(data);
      this.setState({
        template: data,
        isNotifAdmin: notifAdminRes.data.results.length > 0,
      });
    } catch (err) {
      this.setState({ contentError: err });
    } finally {
      this.setState({ hasContentLoading: false });
    }
  }

  async loadTemplate() {
    const { setBreadcrumb, match } = this.props;
    const { id } = match.params;

    this.setState({ contentError: null, hasContentLoading: true });
    try {
      const { data } = await JobTemplatesAPI.readDetail(id);
      setBreadcrumb(data);
      this.setState({ template: data });
    } catch (err) {
      this.setState({ contentError: err });
    } finally {
      this.setState({ hasContentLoading: false });
    }
  }

  render() {
    const { history, i18n, location, match, me } = this.props;
    const {
      contentError,
      hasContentLoading,
      isNotifAdmin,
      template,
    } = this.state;

    const canSeeNotificationsTab = me.is_system_auditor || isNotifAdmin;

    const tabsArray = [
      { name: i18n._(t`Details`), link: `${match.url}/details` },
      { name: i18n._(t`Access`), link: `${match.url}/access` },
    ];

    if (canSeeNotificationsTab) {
      tabsArray.push({
        name: i18n._(t`Notifications`),
        link: `${match.url}/notifications`,
      });
    }

    tabsArray.push(
      {
        name: i18n._(t`Schedules`),
        link: '/home',
      },
      {
        name: i18n._(t`Completed Jobs`),
        link: '/home',
      },
      {
        name: i18n._(t`Survey`),
        link: '/home',
      }
    );

    tabsArray.forEach((tab, n) => {
      tab.id = n;
    });

    let cardHeader = hasContentLoading ? null : (
      <CardHeader style={{ padding: 0 }}>
        <RoutedTabs history={history} tabsArray={tabsArray} />
        <CardCloseButton linkTo="/templates" />
      </CardHeader>
    );

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
                  {i18n._(`Template not found.`)}{' '}
                  <Link to="/templates">{i18n._(`View all Templates.`)}</Link>
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
            <Redirect
              from="/templates/:templateType/:id"
              to="/templates/:templateType/:id/details"
              exact
            />
            {template && (
              <Route
                key="details"
                path="/templates/:templateType/:id/details"
                render={() => (
                  <JobTemplateDetail
                    match={match}
                    hasTemplateLoading={hasContentLoading}
                    template={template}
                  />
                )}
              />
            )}
            {template && (
              <Route
                key="edit"
                path="/templates/:templateType/:id/edit"
                render={() => <JobTemplateEdit template={template} />}
              />
            )}
            {template && (
              <Route
                key="access"
                path="/templates/:templateType/:id/access"
                render={() => (
                  <ResourceAccessList
                    resource={template}
                    apiModel={JobTemplatesAPI}
                  />
                )}
              />
            )}
            {canSeeNotificationsTab && (
              <Route
                path="/templates/:templateType/:id/notifications"
                render={() => (
                  <NotificationList
                    id={Number(match.params.id)}
                    canToggleNotifications={isNotifAdmin}
                    apiModel={JobTemplatesAPI}
                  />
                )}
              />
            )}
            <Route
              key="not-found"
              path="*"
              render={() =>
                !hasContentLoading && (
                  <ContentError isNotFound>
                    {match.params.id && (
                      <Link
                        to={`/templates/${match.params.templateType}/${match.params.id}/details`}
                      >
                        {i18n._(`View Template Details`)}
                      </Link>
                    )}
                  </ContentError>
                )
              }
            />
          </Switch>
        </Card>
      </PageSection>
    );
  }
}

export { Template as _Template };
export default withI18n()(withRouter(Template));
