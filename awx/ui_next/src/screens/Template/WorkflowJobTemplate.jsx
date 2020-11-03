import React, { useEffect, useCallback } from 'react';
import { t } from '@lingui/macro';
import { withI18n } from '@lingui/react';
import { CaretLeftIcon } from '@patternfly/react-icons';
import { Card, PageSection } from '@patternfly/react-core';
import {
  Switch,
  Route,
  Redirect,
  Link,
  useLocation,
  useParams,
  useRouteMatch,
} from 'react-router-dom';
import RoutedTabs from '../../components/RoutedTabs';
import useRequest from '../../util/useRequest';
import AppendBody from '../../components/AppendBody';
import ContentError from '../../components/ContentError';
import FullPage from '../../components/FullPage';
import JobList from '../../components/JobList';
import NotificationList from '../../components/NotificationList';
import { Schedules } from '../../components/Schedule';
import { ResourceAccessList } from '../../components/ResourceAccessList';
import WorkflowJobTemplateDetail from './WorkflowJobTemplateDetail';
import WorkflowJobTemplateEdit from './WorkflowJobTemplateEdit';
import { WorkflowJobTemplatesAPI, OrganizationsAPI } from '../../api';
import TemplateSurvey from './TemplateSurvey';
import { Visualizer } from './WorkflowJobTemplateVisualizer';

function WorkflowJobTemplate({ i18n, me, setBreadcrumb }) {
  const location = useLocation();
  const { id: templateId } = useParams();
  const match = useRouteMatch();

  const {
    result: { isNotifAdmin, template },
    isLoading: hasRolesandTemplateLoading,
    error: rolesAndTemplateError,
    request: loadTemplateAndRoles,
  } = useRequest(
    useCallback(async () => {
      const [{ data }, actions, notifAdminRes] = await Promise.all([
        WorkflowJobTemplatesAPI.readDetail(templateId),
        WorkflowJobTemplatesAPI.readWorkflowJobTemplateOptions(templateId),
        OrganizationsAPI.read({
          page_size: 1,
          role_level: 'notification_admin_role',
        }),
      ]);

      if (actions.data.actions.PUT) {
        if (data.webhook_service && data?.related?.webhook_key) {
          const {
            data: { webhook_key },
          } = await WorkflowJobTemplatesAPI.readWebhookKey(templateId);

          data.webhook_key = webhook_key;
        }
      }
      setBreadcrumb(data);

      return {
        template: data,
        isNotifAdmin: notifAdminRes.data.results.length > 0,
      };
    }, [setBreadcrumb, templateId]),
    { isNotifAdmin: false, template: null }
  );
  useEffect(() => {
    loadTemplateAndRoles();
  }, [loadTemplateAndRoles, location.pathname]);

  const createSchedule = data => {
    return WorkflowJobTemplatesAPI.createSchedule(templateId, data);
  };

  const loadScheduleOptions = () => {
    return WorkflowJobTemplatesAPI.readScheduleOptions(templateId);
  };

  const loadSchedules = params => {
    return WorkflowJobTemplatesAPI.readSchedules(templateId, params);
  };

  const canSeeNotificationsTab = me.is_system_auditor || isNotifAdmin;
  const canAddAndEditSurvey =
    template?.summary_fields?.user_capabilities.edit ||
    template?.summary_fields?.user_capabilities.delete;

  const tabsArray = [
    {
      name: (
        <>
          <CaretLeftIcon />
          {i18n._(t`Back to Templates`)}
        </>
      ),
      link: `/templates`,
      id: 99,
    },
    { name: i18n._(t`Details`), link: `${match.url}/details` },
    { name: i18n._(t`Access`), link: `${match.url}/access` },
  ];

  if (canSeeNotificationsTab) {
    tabsArray.push({
      name: i18n._(t`Notifications`),
      link: `${match.url}/notifications`,
    });
  }

  if (template) {
    tabsArray.push({
      name: i18n._(t`Schedules`),
      link: `${match.url}/schedules`,
    });
  }

  tabsArray.push(
    {
      name: i18n._(t`Visualizer`),
      link: `${match.url}/visualizer`,
    },
    {
      name: i18n._(t`Completed Jobs`),
      link: `${match.url}/completed_jobs`,
    },
    {
      name: canAddAndEditSurvey ? i18n._(t`Survey`) : i18n._(t`View Survey`),
      link: `${match.url}/survey`,
    }
  );

  tabsArray.forEach((tab, n) => {
    tab.id = n;
  });

  let showCardHeader = true;

  if (
    location.pathname.endsWith('edit') ||
    location.pathname.includes('schedules/')
  ) {
    showCardHeader = false;
  }

  const contentError = rolesAndTemplateError;
  if (!hasRolesandTemplateLoading && contentError) {
    return (
      <PageSection>
        <Card>
          <ContentError error={contentError}>
            {contentError.response.status === 404 && (
              <span>
                {i18n._(t`Template not found.`)}{' '}
                <Link to="/templates">{i18n._(t`View all Templates.`)}</Link>
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
        {showCardHeader && <RoutedTabs tabsArray={tabsArray} />}
        <Switch>
          <Redirect
            from="/templates/:templateType/:id"
            to="/templates/:templateType/:id/details"
            exact
          />
          {template && (
            <Route key="details" path="/templates/:templateType/:id/details">
              <WorkflowJobTemplateDetail template={template} />
            </Route>
          )}
          {template && (
            <Route key="edit" path="/templates/:templateType/:id/edit">
              <WorkflowJobTemplateEdit template={template} />
            </Route>
          )}
          {template && (
            <Route key="access" path="/templates/:templateType/:id/access">
              <ResourceAccessList
                resource={template}
                apiModel={WorkflowJobTemplatesAPI}
              />
            </Route>
          )}
          {template && (
            <Route
              key="schedules"
              path="/templates/:templateType/:id/schedules"
            >
              <Schedules
                createSchedule={createSchedule}
                setBreadcrumb={setBreadcrumb}
                unifiedJobTemplate={template}
                loadSchedules={loadSchedules}
                loadScheduleOptions={loadScheduleOptions}
              />
            </Route>
          )}
          {canSeeNotificationsTab && (
            <Route path="/templates/:templateType/:id/notifications">
              <NotificationList
                id={Number(templateId)}
                canToggleNotifications={isNotifAdmin}
                apiModel={WorkflowJobTemplatesAPI}
              />
            </Route>
          )}
          {template && (
            <Route
              key="wfjt-visualizer"
              path="/templates/workflow_job_template/:id/visualizer"
            >
              <AppendBody>
                <FullPage>
                  <Visualizer template={template} />
                </FullPage>
              </AppendBody>
            </Route>
          )}
          {template?.id && (
            <Route path="/templates/:templateType/:id/completed_jobs">
              <JobList
                defaultParams={{
                  workflow_job__workflow_job_template: template.id,
                }}
              />
            </Route>
          )}
          {template && (
            <Route path="/templates/:templateType/:id/survey">
              <TemplateSurvey
                template={template}
                canEdit={canAddAndEditSurvey}
              />
            </Route>
          )}
          {!hasRolesandTemplateLoading && (
            <Route key="not-found" path="*">
              <ContentError isNotFound>
                {match.params.id && (
                  <Link
                    to={`/templates/${match.params.templateType}/${match.params.id}/details`}
                  >
                    {i18n._(t`View Template Details`)}
                  </Link>
                )}
              </ContentError>
            </Route>
          )}
        </Switch>
      </Card>
    </PageSection>
  );
}

export { WorkflowJobTemplate as _WorkflowJobTemplate };
export default withI18n()(WorkflowJobTemplate);
