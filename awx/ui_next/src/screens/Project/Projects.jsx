import React, { Component, Fragment } from 'react';
import { Route, withRouter, Switch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import { Config } from '../../contexts/Config';
import Breadcrumbs from '../../components/Breadcrumbs/Breadcrumbs';

import ProjectsList from './ProjectList/ProjectList';
import ProjectAdd from './ProjectAdd/ProjectAdd';
import Project from './Project';

class Projects extends Component {
  constructor(props) {
    super(props);

    const { i18n } = props;

    this.state = {
      breadcrumbConfig: {
        '/projects': i18n._(t`Projects`),
        '/projects/add': i18n._(t`Create New Project`),
      },
    };
  }

  setBreadcrumbConfig = (project, nested) => {
    const { i18n } = this.props;

    if (!project) {
      return;
    }

    const projectSchedulesPath = `/projects/${project.id}/schedules`;

    const breadcrumbConfig = {
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
    };

    this.setState({ breadcrumbConfig });
  };

  render() {
    const { match, history, location } = this.props;
    const { breadcrumbConfig } = this.state;

    return (
      <Fragment>
        <Breadcrumbs breadcrumbConfig={breadcrumbConfig} />
        <Switch>
          <Route path={`${match.path}/add`}>
            <ProjectAdd />
          </Route>
          <Route path={`${match.path}/:id`}>
            <Config>
              {({ me }) => (
                <Project
                  history={history}
                  location={location}
                  setBreadcrumb={this.setBreadcrumbConfig}
                  me={me || {}}
                />
              )}
            </Config>
          </Route>
          <Route path={`${match.path}`}>
            <ProjectsList />
          </Route>
        </Switch>
      </Fragment>
    );
  }
}

export { Projects as _Projects };
export default withI18n()(withRouter(Projects));
