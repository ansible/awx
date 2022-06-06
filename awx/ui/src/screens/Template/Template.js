import React, { useEffect, useCallback } from 'react';
import { t } from '@lingui/macro';

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
import RoutedTabs from 'components/RoutedTabs';
import { useConfig } from 'contexts/Config';
import useRequest from 'hooks/useRequest';
import ContentError from 'components/ContentError';
import JobList from 'components/JobList';
import NotificationList from 'components/NotificationList';
import { Schedules } from 'components/Schedule';
import { ResourceAccessList } from 'components/ResourceAccessList';
import { JobTemplatesAPI, OrganizationsAPI } from 'api';
import JobTemplateDetail from './JobTemplateDetail';
import JobTemplateEdit from './JobTemplateEdit';
import TemplateSurvey from './TemplateSurvey';

function Template({ setBreadcrumb }) {
  const match = useRouteMatch();
  const location = useLocation();
  const { id: templateId } = useParams();
  const { me = {} } = useConfig();

  const {
    result: {
      isNotifAdmin,
      template,
      surveyConfig,
      launchConfig,
      resourceDefaultCredentials,
    },
    isLoading,
    error: contentError,
    request: loadTemplateAndRoles,
  } = useRequest(
    useCallback(async () => {
      const [
        { data },
        {
          data: { results: defaultCredentials },
        },
        actions,
        notifAdminRes,
        { data: launchConfiguration },
      ] = await Promise.all([
        JobTemplatesAPI.readDetail(templateId),
        JobTemplatesAPI.readCredentials(templateId, {
          page_size: 200,
        }),
        JobTemplatesAPI.readTemplateOptions(templateId),
        OrganizationsAPI.read({
          page_size: 1,
          role_level: 'notification_admin_role',
        }),
        JobTemplatesAPI.readLaunch(templateId),
      ]);
      let surveyConfiguration = {};

      if (data.survey_enabled) {
        const { data: survey } = await JobTemplatesAPI.readSurvey(templateId);

        surveyConfiguration = survey;
      }
      if (data.summary_fields.credentials) {
        data.summary_fields.credentials = defaultCredentials;
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
        surveyConfig: surveyConfiguration,
        launchConfig: launchConfiguration,
        resourceDefaultCredentials: defaultCredentials,
      };
    }, [templateId]),
    { isNotifAdmin: false, template: null, resourceDefaultCredentials: [] }
  );

  useEffect(() => {
    loadTemplateAndRoles();
  }, [loadTemplateAndRoles]);

  useEffect(() => {
    if (template) {
      setBreadcrumb(template);
    }
  }, [template, setBreadcrumb]);

  const loadScheduleOptions = useCallback(
    () => JobTemplatesAPI.readScheduleOptions(templateId),
    [templateId]
  );

  const loadSchedules = useCallback(
    (params) => JobTemplatesAPI.readSchedules(templateId, params),
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
          {t`Back to Templates`}
        </>
      ),
      link: `/templates`,
      isBackButton: true,
      id: 99,
    },
    { name: t`Details`, link: `${match.url}/details` },
    { name: t`Access`, link: `${match.url}/access` },
  ];

  if (canSeeNotificationsTab) {
    tabsArray.push({
      name: t`Notifications`,
      link: `${match.url}/notifications`,
    });
  }

  if (template) {
    tabsArray.push({
      name: t`Schedules`,
      link: `${match.url}/schedules`,
    });
  }

  tabsArray.push(
    {
      name: t`Jobs`,
      link: `${match.url}/jobs`,
    },
    {
      name: canAddAndEditSurvey ? t`Survey` : t`View Survey`,
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
                {t`Template not found.`}{' '}
                <Link to="/templates">{t`View all Templates.`}</Link>
              </span>
            )}
          </ContentError>
        </Card>
      </PageSection>
    );
  }

  const showCardHeader = !(
    location.pathname.endsWith('edit') ||
    location.pathname.includes('schedules/') ||
    location.pathname.includes('survey/')
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
              <JobTemplateEdit
                template={template}
                reloadTemplate={loadTemplateAndRoles}
              />
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
                apiModel={JobTemplatesAPI}
                setBreadcrumb={setBreadcrumb}
                resource={template}
                loadSchedules={loadSchedules}
                loadScheduleOptions={loadScheduleOptions}
                surveyConfig={surveyConfig}
                launchConfig={launchConfig}
                resourceDefaultCredentials={resourceDefaultCredentials}
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
            <Route path="/templates/:templateType/:id/jobs">
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
                      {t`View Template Details`}
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
export default Template;
