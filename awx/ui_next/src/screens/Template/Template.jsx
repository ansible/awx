import React, { useEffect, useCallback } from 'react';
import { t } from '@lingui/macro';
import { withI18n } from '@lingui/react';
import { Card, CardActions, PageSection } from '@patternfly/react-core';
import {
  Switch,
  Route,
  Redirect,
  withRouter,
  Link,
  useLocation,
  useParams,
  useRouteMatch,
} from 'react-router-dom';
import useRequest from '@util/useRequest';

import { TabbedCardHeader } from '@components/Card';
import CardCloseButton from '@components/CardCloseButton';
import ContentError from '@components/ContentError';
import JobList from '@components/JobList';
import NotificationList from '@components/NotificationList';
import RoutedTabs from '@components/RoutedTabs';
import { Schedules } from '@components/Schedule';
import { ResourceAccessList } from '@components/ResourceAccessList';
import JobTemplateDetail from './JobTemplateDetail';
import JobTemplateEdit from './JobTemplateEdit';
import { JobTemplatesAPI, OrganizationsAPI } from '@api';
import TemplateSurvey from './TemplateSurvey';

function Template({ i18n, me, setBreadcrumb }) {
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
      const [{ data }, notifAdminRes] = await Promise.all([
        JobTemplatesAPI.readDetail(templateId),
        OrganizationsAPI.read({
          page_size: 1,
          role_level: 'notification_admin_role',
        }),
      ]);
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
    return JobTemplatesAPI.createSchedule(templateId, data);
  };

  const loadScheduleOptions = () => {
    return JobTemplatesAPI.readScheduleOptions(templateId);
  };

  const loadSchedules = params => {
    return JobTemplatesAPI.readSchedules(templateId, params);
  };

  const canSeeNotificationsTab = me.is_system_auditor || isNotifAdmin;

  const tabsArray = [
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
      name: i18n._(t`Survey`),
      link: `${match.url}/survey`,
    }
  );

  tabsArray.forEach((tab, n) => {
    tab.id = n;
  });

  let cardHeader = (
    <TabbedCardHeader>
      <RoutedTabs tabsArray={tabsArray} />
      <CardActions>
        <CardCloseButton linkTo="/templates" />
      </CardActions>
    </TabbedCardHeader>
  );
  if (
    location.pathname.endsWith('edit') ||
    location.pathname.includes('schedules/')
  ) {
    cardHeader = null;
  }

  const contentError = rolesAndTemplateError;
  if (!hasRolesandTemplateLoading && contentError) {
    return (
      <PageSection>
        <Card>
          <ContentError error={contentError}>
            {contentError.response.status === 404 && (
              <span>
                {i18n._(`Template not found.`)}{' '}
                <Link to="/templates">{i18n._(`View all Templates.`)}</Link>
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
        {cardHeader}
        <Switch>
          <Redirect
            from="/templates/:templateType/:id"
            to="/templates/:templateType/:id/details"
            exact
          />
          {template && (
            <Route key="details" path="/templates/:templateType/:id/details">
              <JobTemplateDetail
                hasTemplateLoading={hasRolesandTemplateLoading}
                template={template}
              />
            </Route>
          )}
          {template && (
            <Route key="edit" path="/templates/:templateType/:id/edit">
              <JobTemplateEdit template={template} />
            </Route>
          )}
          {template && (
            <Route key="access" path="/templates/:templateType/:id/access">
              <ResourceAccessList
                resource={template}
                apiModel={JobTemplatesAPI}
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
                apiModel={JobTemplatesAPI}
              />
            </Route>
          )}
          {template?.id && (
            <Route path="/templates/:templateType/:id/completed_jobs">
              <JobList defaultParams={{ job__job_template: template.id }} />
            </Route>
          )}
          {template && (
            <Route path="/templates/:templateType/:id/survey">
              <TemplateSurvey template={template} />
            </Route>
          )}
          {!hasRolesandTemplateLoading && (
            <Route key="not-found" path="*">
              <ContentError isNotFound>
                {match.params.id && (
                  <Link
                    to={`/templates/${match.params.templateType}/${match.params.id}/details`}
                  >
                    {i18n._(`View Template Details`)}
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

export { Template as _Template };
export default withI18n()(withRouter(Template));
