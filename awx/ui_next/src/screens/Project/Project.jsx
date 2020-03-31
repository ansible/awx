import React, { Component } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Switch, Route, withRouter, Redirect, Link } from 'react-router-dom';
import { Card, CardActions, PageSection } from '@patternfly/react-core';
import { TabbedCardHeader } from '@components/Card';
import CardCloseButton from '@components/CardCloseButton';
import RoutedTabs from '@components/RoutedTabs';
import ContentError from '@components/ContentError';
import NotificationList from '@components/NotificationList';
import { ResourceAccessList } from '@components/ResourceAccessList';
import { Schedules } from '@components/Schedule';
import ProjectDetail from './ProjectDetail';
import ProjectEdit from './ProjectEdit';
import ProjectJobTemplatesList from './ProjectJobTemplatesList';
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
    };
    this.createSchedule = this.createSchedule.bind(this);
    this.loadProject = this.loadProject.bind(this);
    this.loadProjectAndRoles = this.loadProjectAndRoles.bind(this);
    this.loadSchedules = this.loadSchedules.bind(this);
    this.loadScheduleOptions = this.loadScheduleOptions.bind(this);
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
      setBreadcrumb(data);
      this.setState({
        project: data,
        isNotifAdmin: notifAdminRes.data.results.length > 0,
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

  createSchedule(data) {
    const { project } = this.state;
    return ProjectsAPI.createSchedule(project.id, data);
  }

  loadScheduleOptions() {
    const { project } = this.state;
    return ProjectsAPI.readScheduleOptions(project.id);
  }

  loadSchedules(params) {
    const { project } = this.state;
    return ProjectsAPI.readSchedules(project.id, params);
  }

  render() {
    const { location, match, me, i18n, setBreadcrumb } = this.props;

    const {
      project,
      contentError,
      hasContentLoading,
      isInitialized,
      isNotifAdmin,
    } = this.state;
    const canSeeNotificationsTab = me.is_system_auditor || isNotifAdmin;
    const canToggleNotifications = isNotifAdmin;

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

    tabsArray.push({
      name: i18n._(t`Job Templates`),
      link: `${match.url}/job_templates`,
    });

    if (project?.scm_type) {
      tabsArray.push({
        name: i18n._(t`Schedules`),
        link: `${match.url}/schedules`,
      });
    }

    tabsArray.forEach((tab, n) => {
      tab.id = n;
    });

    let cardHeader = (
      <TabbedCardHeader>
        <RoutedTabs tabsArray={tabsArray} />
        <CardActions>
          <CardCloseButton linkTo="/projects" />
        </CardActions>
      </TabbedCardHeader>
    );

    if (!isInitialized) {
      cardHeader = null;
    }

    if (
      location.pathname.endsWith('edit') ||
      location.pathname.includes('schedules/')
    ) {
      cardHeader = null;
    }

    if (!hasContentLoading && contentError) {
      return (
        <PageSection>
          <Card>
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
        <Card>
          {cardHeader}
          <Switch>
            <Redirect from="/projects/:id" to="/projects/:id/details" exact />
            {project && (
              <Route
                path="/projects/:id/edit"
                render={() => <ProjectEdit project={project} />}
              />
            )}
            {project && (
              <Route
                path="/projects/:id/details"
                render={() => <ProjectDetail project={project} />}
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
                <ProjectJobTemplatesList id={Number(match.params.id)} />
              )}
            />
            {project?.scm_type && project.scm_type !== '' && (
              <Route
                path="/projects/:id/schedules"
                render={() => (
                  <Schedules
                    setBreadcrumb={setBreadcrumb}
                    unifiedJobTemplate={project}
                    createSchedule={this.createSchedule}
                    loadSchedules={this.loadSchedules}
                    loadScheduleOptions={this.loadScheduleOptions}
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
