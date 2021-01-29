import React, { useState, useCallback, useRef } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Route, withRouter, Switch } from 'react-router-dom';
import { PageSection } from '@patternfly/react-core';

import ScreenHeader from '../../components/ScreenHeader/ScreenHeader';
import TemplateList from '../../components/TemplateList';
import Template from './Template';
import WorkflowJobTemplate from './WorkflowJobTemplate';
import JobTemplateAdd from './JobTemplateAdd';
import WorkflowJobTemplateAdd from './WorkflowJobTemplateAdd';

function Templates({ i18n }) {
  const initScreenHeader = useRef({
    '/templates': i18n._(t`Templates`),
    '/templates/job_template/add': i18n._(t`Create New Job Template`),
    '/templates/workflow_job_template/add': i18n._(
      t`Create New Workflow Template`
    ),
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
        [`${templatePath}/details`]: i18n._(t`Details`),
        [`${templatePath}/edit`]: i18n._(t`Edit Details`),
        [`${templatePath}/access`]: i18n._(t`Access`),
        [`${templatePath}/notifications`]: i18n._(t`Notifications`),
        [`${templatePath}/completed_jobs`]: i18n._(t`Completed Jobs`),
        [surveyPath]: i18n._(t`Survey`),
        [`${surveyPath}/add`]: i18n._(t`Add Question`),
        [`${surveyPath}/edit`]: i18n._(t`Edit Question`),
        [schedulesPath]: i18n._(t`Schedules`),
        [`${schedulesPath}/add`]: i18n._(t`Create New Schedule`),
        [`${schedulesPath}/${schedule?.id}`]: `${schedule?.name}`,
        [`${schedulesPath}/${schedule?.id}/details`]: i18n._(
          t`Schedule Details`
        ),
        [`${schedulesPath}/${schedule?.id}/edit`]: i18n._(t`Edit Schedule`),
      });
    },
    [i18n, template, schedule]
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
            <TemplateList />
          </PageSection>
        </Route>
      </Switch>
    </>
  );
}

export { Templates as _Templates };
export default withI18n()(withRouter(Templates));
