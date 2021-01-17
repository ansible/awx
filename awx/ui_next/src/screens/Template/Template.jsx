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
import { useConfig } from '../../contexts/Config';
import useRequest from '../../util/useRequest';
import ContentError from '../../components/ContentError';
import JobList from '../../components/JobList';
import NotificationList from '../../components/NotificationList';
import { Schedules } from '../../components/Schedule';
import { ResourceAccessList } from '../../components/ResourceAccessList';
import JobTemplateDetail from './JobTemplateDetail';
import JobTemplateEdit from './JobTemplateEdit';
import { JobTemplatesAPI, OrganizationsAPI } from '../../api';
import TemplateSurvey from './TemplateSurvey';

function Template({ i18n, setBreadcrumb }) {
  const match = useRouteMatch();
  const location = useLocation();
  const { id: templateId } = useParams();
  const { me = {} } = useConfig();

  const {
    result: { isNotifAdmin, template },
    isLoading,
    error: contentError,
    request: loadTemplateAndRoles,
  } = useRequest(
    useCallback(async () => {
      const [{ data }, actions, notifAdminRes] = await Promise.all([
        JobTemplatesAPI.readDetail(templateId),
        JobTemplatesAPI.readTemplateOptions(templateId),
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
        } = await JobTemplatesAPI.readCredentials(data.id, params);

        data.summary_fields.credentials = results;
      }

      if (actions.data.actions.PUT) {
        if (data.webhook_service && data?.related?.webhook_key) {
          const {
            data: { webhook_key },
          } = await JobTemplatesAPI.readWebhookKey(templateId);

          data.webhook_key = webhook_key;
        }
      }
      return {
        template: data,
        isNotifAdmin: notifAdminRes.data.results.length > 0,
      };
    }, [templateId]),
    { isNotifAdmin: false, template: null }
  );

  useEffect(() => {
    loadTemplateAndRoles();
  }, [loadTemplateAndRoles, location.pathname]);

  useEffect(() => {
    if (template) {
      setBreadcrumb(template);
    }
  }, [template, setBreadcrumb]);

  const createSchedule = data => {
    return JobTemplatesAPI.createSchedule(template.id, data);
  };

  const loadScheduleOptions = useCallback(() => {
    return JobTemplatesAPI.readScheduleOptions(templateId);
  }, [templateId]);

  const loadSchedules = useCallback(
    params => {
      return JobTemplatesAPI.readSchedules(templateId, params);
    },
    [templateId]
  );

  const canSeeNotificationsTab = me?.is_system_auditor || isNotifAdmin;
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

  if (contentError) {
    return (
      <PageSection>
        <Card>
          <ContentError error={contentError}>
            {contentError.response?.status === 404 && (
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

  const showCardHeader = !(
    location.pathname.endsWith('edit') ||
    location.pathname.includes('schedules/')
  );

  return (
    <PageSection>
      <Card>
        {showCardHeader && <RoutedTabs tabsArray={tabsArray} />}
        {template && (
          <Switch>
            <Redirect
              from="/templates/:templateType/:id"
              to="/templates/:templateType/:id/details"
              exact
            />
            <Route key="details" path="/templates/:templateType/:id/details">
              <JobTemplateDetail
                hasTemplateLoading={isLoading}
                template={template}
              />
            </Route>
            <Route key="edit" path="/templates/:templateType/:id/edit">
              <JobTemplateEdit template={template} />
            </Route>
            <Route key="access" path="/templates/:templateType/:id/access">
              <ResourceAccessList
                resource={template}
                apiModel={JobTemplatesAPI}
              />
            </Route>
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
            {canSeeNotificationsTab && (
              <Route path="/templates/:templateType/:id/notifications">
                <NotificationList
                  id={Number(templateId)}
                  canToggleNotifications={isNotifAdmin}
                  apiModel={JobTemplatesAPI}
                />
              </Route>
            )}
            <Route path="/templates/:templateType/:id/completed_jobs">
              <JobList defaultParams={{ job__job_template: template.id }} />
            </Route>
            <Route path="/templates/:templateType/:id/survey">
              <TemplateSurvey
                template={template}
                canEdit={canAddAndEditSurvey}
              />
            </Route>
            {!isLoading && (
              <Route key="not-found" path="*">
                <ContentError isNotFound>
                  {match.params.id && (
                    <Link
                      to={`/templates/${match?.params?.templateType}/${templateId}/details`}
                    >
                      {i18n._(t`View Template Details`)}
                    </Link>
                  )}
                </ContentError>
              </Route>
            )}
          </Switch>
        )}
      </Card>
    </PageSection>
  );
}

export { Template as _Template };
export default withI18n()(Template);
