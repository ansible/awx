import React, { useState, useCallback } from 'react';
import { Route, withRouter, Switch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import ScreenHeader from '../../components/ScreenHeader/ScreenHeader';

import ProjectsList from './ProjectList/ProjectList';
import ProjectAdd from './ProjectAdd/ProjectAdd';
import Project from './Project';

function Projects({ i18n }) {
  const [breadcrumbConfig, setBreadcrumbConfig] = useState({
    '/projects': i18n._(t`Projects`),
    '/projects/add': i18n._(t`Create New Project`),
  });

  const buildBreadcrumbConfig = useCallback(
    (project, nested) => {
      if (!project) {
        return;
      }
      const projectSchedulesPath = `/projects/${project.id}/schedules`;
      setBreadcrumbConfig({
        '/projects': i18n._(t`Projects`),
        '/projects/add': i18n._(t`Create New Project`),
        [`/projects/${project.id}`]: `${project.name}`,
        [`/projects/${project.id}/edit`]: i18n._(t`Edit Details`),
        [`/projects/${project.id}/details`]: i18n._(t`Details`),
        [`/projects/${project.id}/access`]: i18n._(t`Access`),
        [`/projects/${project.id}/notifications`]: i18n._(t`Notifications`),
        [`/projects/${project.id}/job_templates`]: i18n._(t`Job Templates`),

        [`${projectSchedulesPath}`]: i18n._(t`Schedules`),
        [`${projectSchedulesPath}/add`]: i18n._(t`Create New Schedule`),
        [`${projectSchedulesPath}/${nested?.id}`]: `${nested?.name}`,
        [`${projectSchedulesPath}/${nested?.id}/details`]: i18n._(
          t`Schedule Details`
        ),
        [`${projectSchedulesPath}/${nested?.id}/edit`]: i18n._(t`Edit Details`),
      });
    },
    [i18n]
  );

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
          <ProjectsList />
        </Route>
      </Switch>
    </>
  );
}

export { Projects as _Projects };
export default withI18n()(withRouter(Projects));
