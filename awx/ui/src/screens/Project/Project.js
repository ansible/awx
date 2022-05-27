import React, { useCallback, useEffect } from 'react';

import { t } from '@lingui/macro';
import {
  Switch,
  Route,
  Redirect,
  Link,
  useParams,
  useLocation,
} from 'react-router-dom';
import { CaretLeftIcon } from '@patternfly/react-icons';
import { Card, PageSection } from '@patternfly/react-core';
import { useConfig } from 'contexts/Config';
import useRequest from 'hooks/useRequest';
import RoutedTabs from 'components/RoutedTabs';
import ContentError from 'components/ContentError';
import ContentLoading from 'components/ContentLoading';
import NotificationList from 'components/NotificationList';
import { ResourceAccessList } from 'components/ResourceAccessList';
import { Schedules } from 'components/Schedule';
import RelatedTemplateList from 'components/RelatedTemplateList';
import { OrganizationsAPI, ProjectsAPI } from 'api';
import ProjectDetail from './ProjectDetail';
import ProjectEdit from './ProjectEdit';

function Project({ setBreadcrumb }) {
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

  const loadScheduleOptions = useCallback(
    () => ProjectsAPI.readScheduleOptions(project.id),
    [project]
  );

  const loadSchedules = useCallback(
    (params) => ProjectsAPI.readSchedules(project.id, params),
    [project]
  );

  const canSeeNotificationsTab = me.is_system_auditor || isNotifAdmin;
  const canToggleNotifications = isNotifAdmin;
  const tabsArray = [
    {
      name: (
        <>
          <CaretLeftIcon />
          {t`Back to Projects`}
        </>
      ),
      link: `/projects`,
      id: 99,
    },
    { name: t`Details`, link: `/projects/${id}/details` },
    { name: t`Access`, link: `/projects/${id}/access` },
    {
      name: t`Job Templates`,
      link: `/projects/${id}/job_templates`,
    },
  ];

  if (canSeeNotificationsTab) {
    tabsArray.push({
      name: t`Notifications`,
      link: `/projects/${id}/notifications`,
    });
  }
  if (project?.scm_type) {
    tabsArray.push({
      name: t`Schedules`,
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
                {t`Project not found.`}{' '}
                <Link to="/projects">{t`View all Projects.`}</Link>
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
              <RelatedTemplateList
                searchParams={{
                  project__id: project.id,
                }}
                projectName={project.name}
              />
            </Route>
            {project?.scm_type && project.scm_type !== '' && (
              <Route path="/projects/:id/schedules">
                <Schedules
                  setBreadcrumb={setBreadcrumb}
                  resource={project}
                  apiModel={ProjectsAPI}
                  loadSchedules={loadSchedules}
                  loadScheduleOptions={loadScheduleOptions}
                />
              </Route>
            )}
            <Route key="not-found" path="*">
              <ContentError isNotFound>
                {id && (
                  <Link to={`/projects/${id}/details`}>
                    {t`View Project Details`}
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

export default Project;
export { Project as _Project };
