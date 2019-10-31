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
import NotificationList from '@components/NotificationList';
import { ResourceAccessList } from '@components/ResourceAccessList';
import ProjectDetail from './ProjectDetail';
import ProjectEdit from './ProjectEdit';
import ProjectJobTemplates from './ProjectJobTemplates';
import ProjectSchedules from './ProjectSchedules';
import { OrganizationsAPI, ProjectsAPI } from '@api';

class Project extends Component {
  constructor(props) {
    super(props);

    this.state = {
      project: null,
      hasContentLoading: true,
      contentError: null,
      isInitialized: false,
      isNotifAdmin: false,
      isAuditorOfThisOrg: false,
      isAdminOfThisOrg: false,
    };
    this.loadProject = this.loadProject.bind(this);
    this.loadProjectAndRoles = this.loadProjectAndRoles.bind(this);
  }

  async componentDidMount() {
    await this.loadProjectAndRoles();
    this.setState({ isInitialized: true });
  }

  async componentDidUpdate(prevProps) {
    const { location, match } = this.props;
    const url = `/projects/${match.params.id}/`;

    if (
      prevProps.location.pathname.startsWith(url) &&
      prevProps.location !== location &&
      location.pathname === `${url}details`
    ) {
      await this.loadProject();
    }
  }

  async loadProjectAndRoles() {
    const { match, setBreadcrumb } = this.props;
    const id = parseInt(match.params.id, 10);

    this.setState({ contentError: null, hasContentLoading: true });
    try {
      const [{ data }, notifAdminRes] = await Promise.all([
        ProjectsAPI.readDetail(id),
        OrganizationsAPI.read({
          page_size: 1,
          role_level: 'notification_admin_role',
        }),
      ]);
      const [auditorRes, adminRes] = await Promise.all([
        OrganizationsAPI.read({
          id: data.organization,
          role_level: 'auditor_role',
        }),
        OrganizationsAPI.read({
          id: data.organization,
          role_level: 'admin_role',
        }),
      ]);
      setBreadcrumb(data);
      this.setState({
        project: data,
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

  async loadProject() {
    const { match, setBreadcrumb } = this.props;
    const id = parseInt(match.params.id, 10);

    this.setState({ contentError: null, hasContentLoading: true });
    try {
      const { data } = await ProjectsAPI.readDetail(id);
      setBreadcrumb(data);
      this.setState({ project: data });
    } catch (err) {
      this.setState({ contentError: err });
    } finally {
      this.setState({ hasContentLoading: false });
    }
  }

  render() {
    const { location, match, me, history, i18n } = this.props;

    const {
      project,
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
        name: i18n._(t`Job Templates`),
        link: `${match.url}/job_templates`,
      },
      {
        name: i18n._(t`Schedules`),
        link: `${match.url}/schedules`,
      }
    );

    tabsArray.forEach((tab, n) => {
      tab.id = n;
    });

    const CardHeader = styled(PFCardHeader)`
      --pf-c-card--first-child--PaddingTop: 0;
      --pf-c-card--child--PaddingLeft: 0;
      --pf-c-card--child--PaddingRight: 0;
      position: relative;
    `;

    let cardHeader = (
      <CardHeader style={{ padding: 0 }}>
        <RoutedTabs
          match={match}
          history={history}
          labeltext={i18n._(t`Project detail tabs`)}
          tabsArray={tabsArray}
        />
        <CardCloseButton linkTo="/projects" />
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
                  {i18n._(`Project not found.`)}{' '}
                  <Link to="/projects">{i18n._(`View all Projects.`)}</Link>
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
            <Redirect from="/projects/:id" to="/projects/:id/details" exact />
            {project && (
              <Route
                path="/projects/:id/edit"
                render={() => <ProjectEdit match={match} project={project} />}
              />
            )}
            {project && (
              <Route
                path="/projects/:id/details"
                render={() => <ProjectDetail match={match} project={project} />}
              />
            )}
            {project && (
              <Route
                path="/projects/:id/access"
                render={() => (
                  <ResourceAccessList
                    resource={project}
                    apiModel={ProjectsAPI}
                  />
                )}
              />
            )}
            {canSeeNotificationsTab && (
              <Route
                path="/projects/:id/notifications"
                render={() => (
                  <NotificationList
                    id={Number(match.params.id)}
                    canToggleNotifications={canToggleNotifications}
                    apiModel={ProjectsAPI}
                  />
                )}
              />
            )}
            <Route
              path="/projects/:id/job_templates"
              render={() => (
                <ProjectJobTemplates id={Number(match.params.id)} />
              )}
            />
            <Route
              path="/projects/:id/schedules"
              render={() => <ProjectSchedules id={Number(match.params.id)} />}
            />
            <Route
              key="not-found"
              path="*"
              render={() =>
                !hasContentLoading && (
                  <ContentError isNotFound>
                    {match.params.id && (
                      <Link to={`/projects/${match.params.id}/details`}>
                        {i18n._(`View Project Details`)}
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

export default withI18n()(withRouter(Project));
export { Project as _Project };
