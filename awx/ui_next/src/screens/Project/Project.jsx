import React, { useCallback, useEffect } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  Switch,
  Route,
  withRouter,
  Redirect,
  Link,
  useParams,
  useLocation,
} from 'react-router-dom';
import { CaretLeftIcon } from '@patternfly/react-icons';
import { Card, PageSection } from '@patternfly/react-core';
import { useConfig } from '../../contexts/Config';
import useRequest from '../../util/useRequest';
import RoutedTabs from '../../components/RoutedTabs';
import ContentError from '../../components/ContentError';
import ContentLoading from '../../components/ContentLoading';
import NotificationList from '../../components/NotificationList';
import { ResourceAccessList } from '../../components/ResourceAccessList';
import { Schedules } from '../../components/Schedule';
import ProjectDetail from './ProjectDetail';
import ProjectEdit from './ProjectEdit';
import ProjectJobTemplatesList from './ProjectJobTemplatesList';
import { OrganizationsAPI, ProjectsAPI } from '../../api';

function Project({ i18n, setBreadcrumb }) {
  const { me = {} } = useConfig();
  const { id } = useParams();
  const location = useLocation();

  const {
    request: fetchProjectAndRoles,
    result: { project, isNotifAdmin },
    isLoading: hasContentLoading,
    error: contentError,
  } = useRequest(
    useCallback(async () => {
      const [{ data }, notifAdminRes] = await Promise.all([
        ProjectsAPI.readDetail(id),
        OrganizationsAPI.read({
          page_size: 1,
          role_level: 'notification_admin_role',
        }),
      ]);

      if (data.summary_fields.credentials) {
        const params = {
          page: 1,
          page_size: 200,
          order_by: 'name',
        };
        const {
          data: { results },
        } = await ProjectsAPI.readCredentials(data.id, params);

        data.summary_fields.credentials = results;
      }
      return {
        project: data,
        isNotifAdmin: notifAdminRes.data.results.length > 0,
      };
    }, [id]),
    {
      project: null,
      notifAdminRes: null,
    }
  );

  useEffect(() => {
    fetchProjectAndRoles();
  }, [fetchProjectAndRoles, location.pathname]);

  useEffect(() => {
    if (project) {
      setBreadcrumb(project);
    }
  }, [project, setBreadcrumb]);

  function createSchedule(data) {
    return ProjectsAPI.createSchedule(project.id, data);
  }

  const loadScheduleOptions = useCallback(() => {
    return ProjectsAPI.readScheduleOptions(project.id);
  }, [project]);

  const loadSchedules = useCallback(
    params => {
      return ProjectsAPI.readSchedules(project.id, params);
    },
    [project]
  );

  const canSeeNotificationsTab = me.is_system_auditor || isNotifAdmin;
  const canToggleNotifications = isNotifAdmin;
  const tabsArray = [
    {
      name: (
        <>
          <CaretLeftIcon />
          {i18n._(t`Back to Projects`)}
        </>
      ),
      link: `/projects`,
      id: 99,
    },
    { name: i18n._(t`Details`), link: `/projects/${id}/details` },
    { name: i18n._(t`Access`), link: `/projects/${id}/access` },
  ];

  if (canSeeNotificationsTab) {
    tabsArray.push({
      name: i18n._(t`Notifications`),
      link: `/projects/${id}/notifications`,
    });
  }

  tabsArray.push({
    name: i18n._(t`Job Templates`),
    link: `/projects/${id}/job_templates`,
  });

  if (project?.scm_type) {
    tabsArray.push({
      name: i18n._(t`Schedules`),
      link: `/projects/${id}/schedules`,
    });
  }

  tabsArray.forEach((tab, n) => {
    tab.id = n;
  });

  if (contentError) {
    return (
      <PageSection>
        <Card>
          <ContentError error={contentError}>
            {contentError.response.status === 404 && (
              <span>
                {i18n._(t`Project not found.`)}{' '}
                <Link to="/projects">{i18n._(t`View all Projects.`)}</Link>
              </span>
            )}
          </ContentError>
        </Card>
      </PageSection>
    );
  }

  const showCardHeader = !(
    location.pathname.endsWith('edit') ||
    location.pathname.includes('schedules/')
  );

  return (
    <PageSection>
      <Card>
        {showCardHeader && <RoutedTabs tabsArray={tabsArray} />}
        {hasContentLoading && <ContentLoading />}
        {!hasContentLoading && project && (
          <Switch>
            <Redirect from="/projects/:id" to="/projects/:id/details" exact />
            <Route path="/projects/:id/edit">
              <ProjectEdit project={project} />
            </Route>
            <Route path="/projects/:id/details">
              <ProjectDetail project={project} />
            </Route>
            <Route path="/projects/:id/access">
              <ResourceAccessList resource={project} apiModel={ProjectsAPI} />
            </Route>
            {canSeeNotificationsTab && (
              <Route path="/projects/:id/notifications">
                <NotificationList
                  id={Number(id)}
                  canToggleNotifications={canToggleNotifications}
                  apiModel={ProjectsAPI}
                />
              </Route>
            )}
            <Route path="/projects/:id/job_templates">
              <ProjectJobTemplatesList />
            </Route>
            {project?.scm_type && project.scm_type !== '' && (
              <Route path="/projects/:id/schedules">
                <Schedules
                  setBreadcrumb={setBreadcrumb}
                  unifiedJobTemplate={project}
                  createSchedule={createSchedule}
                  loadSchedules={loadSchedules}
                  loadScheduleOptions={loadScheduleOptions}
                />
              </Route>
            )}
            <Route key="not-found" path="*">
              <ContentError isNotFound>
                {id && (
                  <Link to={`/projects/${id}/details`}>
                    {i18n._(t`View Project Details`)}
                  </Link>
                )}
              </ContentError>
            </Route>
          </Switch>
        )}
      </Card>
    </PageSection>
  );
}

export default withI18n()(withRouter(Project));
export { Project as _Project };
