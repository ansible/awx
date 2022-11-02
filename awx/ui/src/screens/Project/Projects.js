import React, { useState, useCallback } from 'react';
import { Route, withRouter, Switch } from 'react-router-dom';
import { t } from '@lingui/macro';
import ScreenHeader from 'components/ScreenHeader/ScreenHeader';
import PersistentFilters from 'components/PersistentFilters';
import ProjectsList from './ProjectList/ProjectList';
import ProjectAdd from './ProjectAdd/ProjectAdd';
import Project from './Project';

function Projects() {
  const [breadcrumbConfig, setBreadcrumbConfig] = useState({
    '/projects': t`Projects`,
    '/projects/add': t`Create New Project`,
  });

  const buildBreadcrumbConfig = useCallback((project, nested) => {
    if (!project) {
      return;
    }
    const projectSchedulesPath = `/projects/${project.id}/schedules`;
    setBreadcrumbConfig({
      '/projects': t`Projects`,
      '/projects/add': t`Create New Project`,
      [`/projects/${project.id}`]: `${project.name}`,
      [`/projects/${project.id}/edit`]: t`Edit Details`,
      [`/projects/${project.id}/details`]: t`Details`,
      [`/projects/${project.id}/access`]: t`Access`,
      [`/projects/${project.id}/notifications`]: t`Notifications`,
      [`/projects/${project.id}/job_templates`]: t`Job Templates`,

      [`${projectSchedulesPath}`]: t`Schedules`,
      [`${projectSchedulesPath}/add`]: t`Create New Schedule`,
      [`${projectSchedulesPath}/${nested?.id}`]: `${nested?.name}`,
      [`${projectSchedulesPath}/${nested?.id}/details`]: t`Schedule Details`,
      [`${projectSchedulesPath}/${nested?.id}/edit`]: t`Edit Details`,
    });
  }, []);

  return (
    <>
      <ScreenHeader streamType="project" breadcrumbConfig={breadcrumbConfig} />
      <Switch>
        <Route path="/projects/add">
          <ProjectAdd />
        </Route>
        <Route path="/projects/:id">
          <Project setBreadcrumb={buildBreadcrumbConfig} />
        </Route>
        <Route path="/projects">
          <PersistentFilters pageKey="projects">
            <ProjectsList />
          </PersistentFilters>
        </Route>
      </Switch>
    </>
  );
}

export { Projects as _Projects };
export default withRouter(Projects);
