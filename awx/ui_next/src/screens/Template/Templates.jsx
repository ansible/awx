import React, { useState } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Route, withRouter, Switch, useRouteMatch } from 'react-router-dom';
import { PageSection } from '@patternfly/react-core';

import { Config } from '../../contexts/Config';
import Breadcrumbs from '../../components/Breadcrumbs/Breadcrumbs';
import { TemplateList } from './TemplateList';
import Template from './Template';
import WorkflowJobTemplate from './WorkflowJobTemplate';
import JobTemplateAdd from './JobTemplateAdd';
import WorkflowJobTemplateAdd from './WorkflowJobTemplateAdd';

function Templates({ i18n }) {
  const match = useRouteMatch();
  const [breadcrumbConfig, setBreadcrumbs] = useState({
    '/templates': i18n._(t`Templates`),
    '/templates/job_template/add': i18n._(t`Create New Job Template`),
    '/templates/workflow_job_template/add': i18n._(
      t`Create New Workflow Template`
    ),
  });

  const setBreadCrumbConfig = (template, schedule) => {
    if (!template) {
      return;
    }
    const breadcrumb = {
      '/templates': i18n._(t`Templates`),
      '/templates/job_template/add': i18n._(t`Create New Job Template`),
      '/templates/workflow_job_template/add': i18n._(
        t`Create New Workflow Template`
      ),
      [`/templates/${template.type}/${template.id}`]: `${template.name}`,
      [`/templates/${template.type}/${template.id}/details`]: i18n._(
        t`Details`
      ),
      [`/templates/${template.type}/${template.id}/edit`]: i18n._(
        t`Edit Details`
      ),
      [`/templates/${template.type}/${template.id}/access`]: i18n._(t`Access`),
      [`/templates/${template.type}/${template.id}/notifications`]: i18n._(
        t`Notifications`
      ),
      [`/templates/${template.type}/${template.id}/completed_jobs`]: i18n._(
        t`Completed Jobs`
      ),
      [`/templates/${template.type}/${template.id}/survey`]: i18n._(t`Survey`),
      [`/templates/${template.type}/${template.id}/survey/add`]: i18n._(
        t`Add Question`
      ),
      [`/templates/${template.type}/${template.id}/survey/edit`]: i18n._(
        t`Edit Question`
      ),
      [`/templates/${template.type}/${template.id}/schedules`]: i18n._(
        t`Schedules`
      ),
      [`/templates/${template.type}/${template.id}/schedules/add`]: i18n._(
        t`Create New Schedule`
      ),
      [`/templates/${template.type}/${template.id}/schedules/${schedule &&
        schedule.id}`]: `${schedule && schedule.name}`,
      [`/templates/${template.type}/${template.id}/schedules/${schedule &&
        schedule.id}/details`]: i18n._(t`Schedule Details`),
      [`/templates/${template.type}/${template.id}/schedules/${schedule &&
        schedule.id}/edit`]: i18n._(t`Edit Details`),
    };
    setBreadcrumbs(breadcrumb);
  };

  return (
    <>
      <Breadcrumbs breadcrumbConfig={breadcrumbConfig} />
      <Switch>
        <Route path={`${match.path}/job_template/add`}>
          <JobTemplateAdd />
        </Route>
        <Route path={`${match.path}/workflow_job_template/add`}>
          <WorkflowJobTemplateAdd />
        </Route>
        <Route
          path={`${match.path}/job_template/:id`}
          render={({ match: newRouteMatch }) => (
            <Config>
              {({ me }) => (
                <Template
                  setBreadcrumb={setBreadCrumbConfig}
                  me={me || {}}
                  match={newRouteMatch}
                />
              )}
            </Config>
          )}
        />
        <Route
          path={`${match.path}/workflow_job_template/:id`}
          render={({ match: newRouteMatch }) => (
            <Config>
              {({ me }) => (
                <WorkflowJobTemplate
                  setBreadcrumb={setBreadCrumbConfig}
                  me={me || {}}
                  match={newRouteMatch}
                />
              )}
            </Config>
          )}
        />
        <Route path={`${match.path}`}>
          <PageSection>
            <TemplateList />
          </PageSection>
        </Route>
      </Switch>
    </>
  );
}

export { Templates as _Templates };
export default withI18n()(withRouter(Templates));
