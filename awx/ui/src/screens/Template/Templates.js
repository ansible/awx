import React, { useState, useCallback, useRef } from 'react';

import { t } from '@lingui/macro';
import { Route, withRouter, Switch } from 'react-router-dom';
import { PageSection } from '@patternfly/react-core';

import ScreenHeader from 'components/ScreenHeader/ScreenHeader';
import TemplateList from 'components/TemplateList';
import PersistentFilters from 'components/PersistentFilters';
import Template from './Template';
import WorkflowJobTemplate from './WorkflowJobTemplate';
import JobTemplateAdd from './JobTemplateAdd';
import WorkflowJobTemplateAdd from './WorkflowJobTemplateAdd';

function Templates() {
  const initScreenHeader = useRef({
    '/templates': t`Templates`,
    '/templates/job_template/add': t`Create New Job Template`,
    '/templates/workflow_job_template/add': t`Create New Workflow Template`,
  });
  const [breadcrumbConfig, setScreenHeader] = useState(
    initScreenHeader.current
  );

  const [schedule, setSchedule] = useState();
  const [template, setTemplate] = useState();

  const setBreadcrumbConfig = useCallback(
    (passedTemplate, passedSchedule) => {
      if (passedTemplate && passedTemplate.name !== template?.name) {
        setTemplate(passedTemplate);
      }
      if (passedSchedule && passedSchedule.name !== schedule?.name) {
        setSchedule(passedSchedule);
      }
      if (!template) return;
      const templatePath = `/templates/${template.type}/${template.id}`;
      const schedulesPath = `${templatePath}/schedules`;
      const surveyPath = `${templatePath}/survey`;
      setScreenHeader({
        ...initScreenHeader.current,
        [templatePath]: `${template.name}`,
        [`${templatePath}/details`]: t`Details`,
        [`${templatePath}/edit`]: t`Edit Details`,
        [`${templatePath}/access`]: t`Access`,
        [`${templatePath}/notifications`]: t`Notifications`,
        [`${templatePath}/jobs`]: t`Jobs`,
        [surveyPath]: t`Survey`,
        [`${surveyPath}/add`]: t`Add Question`,
        [`${surveyPath}/edit`]: t`Edit Question`,
        [schedulesPath]: t`Schedules`,
        [`${schedulesPath}/add`]: t`Create New Schedule`,
        [`${schedulesPath}/${schedule?.id}`]: `${schedule?.name}`,
        [`${schedulesPath}/${schedule?.id}/details`]: t`Schedule Details`,
        [`${schedulesPath}/${schedule?.id}/edit`]: t`Edit Schedule`,
      });
    },
    [template, schedule]
  );

  return (
    <>
      <ScreenHeader
        streamType="job_template,workflow_job_template,workflow_job_template_node"
        breadcrumbConfig={breadcrumbConfig}
      />
      <Switch>
        <Route path="/templates/job_template/add">
          <JobTemplateAdd />
        </Route>
        <Route path="/templates/workflow_job_template/add">
          <WorkflowJobTemplateAdd />
        </Route>
        <Route path="/templates/job_template/:id">
          <Template setBreadcrumb={setBreadcrumbConfig} />
        </Route>
        <Route path="/templates/workflow_job_template/:id">
          <WorkflowJobTemplate setBreadcrumb={setBreadcrumbConfig} />
        </Route>
        <Route path="/templates">
          <PageSection>
            <PersistentFilters pageKey="templates">
              <TemplateList />
            </PersistentFilters>
          </PageSection>
        </Route>
      </Switch>
    </>
  );
}

export { Templates as _Templates };
export default withRouter(Templates);
