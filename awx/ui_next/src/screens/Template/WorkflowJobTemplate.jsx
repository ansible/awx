import React, { Component } from 'react';
import { t } from '@lingui/macro';
import { withI18n } from '@lingui/react';
import { Card, CardActions, PageSection } from '@patternfly/react-core';
import { Switch, Route, Redirect, withRouter, Link } from 'react-router-dom';
import { TabbedCardHeader } from '@components/Card';
import AppendBody from '@components/AppendBody';
import CardCloseButton from '@components/CardCloseButton';
import ContentError from '@components/ContentError';
import FullPage from '@components/FullPage';
import JobList from '@components/JobList';
import RoutedTabs from '@components/RoutedTabs';
import { Schedules } from '@components/Schedule';
import ContentLoading from '@components/ContentLoading';
import { ResourceAccessList } from '@components/ResourceAccessList';
import NotificationList from '@components/NotificationList';
import {
  WorkflowJobTemplatesAPI,
  CredentialsAPI,
  OrganizationsAPI,
} from '@api';
import WorkflowJobTemplateDetail from './WorkflowJobTemplateDetail';
import WorkflowJobTemplateEdit from './WorkflowJobTemplateEdit';
import { Visualizer } from './WorkflowJobTemplateVisualizer';

class WorkflowJobTemplate extends Component {
  constructor(props) {
    super(props);

    this.state = {
      contentError: null,
      hasContentLoading: true,
      template: null,
      webhook_key: null,
      isNotifAdmin: false,
    };
    this.createSchedule = this.createSchedule.bind(this);
    this.loadTemplate = this.loadTemplate.bind(this);
    this.loadSchedules = this.loadSchedules.bind(this);
    this.loadScheduleOptions = this.loadScheduleOptions.bind(this);
  }

  async componentDidMount() {
    await this.loadTemplate();
  }

  async componentDidUpdate(prevProps) {
    const { location } = this.props;
    if (location !== prevProps.location) {
      await this.loadTemplate();
    }
  }

  async loadTemplate() {
    const { setBreadcrumb, match } = this.props;
    const { id } = match.params;

    this.setState({ contentError: null });
    try {
      const { data } = await WorkflowJobTemplatesAPI.readDetail(id);
      if (data?.related?.webhook_key) {
        const {
          data: { webhook_key },
        } = await WorkflowJobTemplatesAPI.readWebhookKey(id);
        this.setState({ webhook_key });
      }
      if (data?.summary_fields?.webhook_credential) {
        const {
          data: {
            summary_fields: {
              credential_type: { name },
            },
          },
        } = await CredentialsAPI.readDetail(
          data.summary_fields.webhook_credential.id
        );
        data.summary_fields.webhook_credential.kind = name;
      }
      const notifAdminRes = await OrganizationsAPI.read({
        page_size: 1,
        role_level: 'notification_admin_role',
      });
      setBreadcrumb(data);
      this.setState({
        template: data,
        isNotifAdmin: notifAdminRes.data.results.length > 0,
      });
    } catch (err) {
      this.setState({ contentError: err });
    } finally {
      this.setState({ hasContentLoading: false });
    }
  }

  createSchedule(data) {
    const { template } = this.state;
    return WorkflowJobTemplatesAPI.createSchedule(template.id, data);
  }

  loadScheduleOptions() {
    const { template } = this.state;
    return WorkflowJobTemplatesAPI.readScheduleOptions(template.id);
  }

  loadSchedules(params) {
    const { template } = this.state;
    return WorkflowJobTemplatesAPI.readSchedules(template.id, params);
  }

  render() {
    const { i18n, me, location, match, setBreadcrumb } = this.props;
    const {
      contentError,
      hasContentLoading,
      template,
      webhook_key,
      isNotifAdmin,
    } = this.state;

    const canSeeNotificationsTab = me.is_system_auditor || isNotifAdmin;
    const canToggleNotifications = isNotifAdmin;

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

    tabsArray.push({
      name: i18n._(t`Visualizer`),
      link: `${match.url}/visualizer`,
    });
    tabsArray.push({
      name: i18n._(t`Completed Jobs`),
      link: `${match.url}/completed_jobs`,
    });

    tabsArray.forEach((tab, n) => {
      tab.id = n;
    });

    if (hasContentLoading) {
      return (
        <PageSection>
          <Card>
            <ContentLoading />
          </Card>
        </PageSection>
      );
    }

    if (contentError) {
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

    const cardHeader = (
      <TabbedCardHeader>
        <RoutedTabs tabsArray={tabsArray} />
        <CardActions>
          <CardCloseButton linkTo="/templates" />
        </CardActions>
      </TabbedCardHeader>
    );

    return (
      <PageSection>
        <Card>
          {location.pathname.endsWith('edit') ||
          location.pathname.includes('schedules/')
            ? null
            : cardHeader}
          <Switch>
            <Redirect
              from="/templates/workflow_job_template/:id"
              to="/templates/workflow_job_template/:id/details"
              exact
            />
            {template && (
              <Route
                key="wfjt-details"
                path="/templates/workflow_job_template/:id/details"
                render={() => (
                  <WorkflowJobTemplateDetail
                    template={template}
                    webhook_key={webhook_key}
                  />
                )}
              />
            )}
            {template && (
              <Route
                path="/templates/workflow_job_template/:id/access"
                render={() => (
                  <ResourceAccessList
                    resource={template}
                    apiModel={WorkflowJobTemplatesAPI}
                  />
                )}
              />
            )}
            {canSeeNotificationsTab && (
              <Route
                path="/templates/workflow_job_template/:id/notifications"
                render={() => (
                  <NotificationList
                    id={Number(match.params.id)}
                    canToggleNotifications={canToggleNotifications}
                    apiModel={WorkflowJobTemplatesAPI}
                  />
                )}
              />
            )}
            {template && (
              <Route
                key="wfjt-edit"
                path="/templates/workflow_job_template/:id/edit"
                render={() => (
                  <WorkflowJobTemplateEdit
                    template={template}
                    webhook_key={webhook_key}
                  />
                )}
              />
            )}
            {template && (
              <Route
                key="wfjt-visualizer"
                path="/templates/workflow_job_template/:id/visualizer"
                render={() => (
                  <AppendBody>
                    <FullPage>
                      <Visualizer template={template} />
                    </FullPage>
                  </AppendBody>
                )}
              />
            )}
            {template?.id && (
              <Route path="/templates/workflow_job_template/:id/completed_jobs">
                <JobList
                  defaultParams={{
                    workflow_job__workflow_job_template: template.id,
                  }}
                />
              </Route>
            )}
            {template?.id && (
              <Route
                path="/templates/workflow_job_template/:id/schedules"
                render={() => (
                  <Schedules
                    setBreadcrumb={setBreadcrumb}
                    unifiedJobTemplate={template}
                    createSchedule={this.createSchedule}
                    loadSchedules={this.loadSchedules}
                    loadScheduleOptions={this.loadScheduleOptions}
                  />
                )}
              />
            )}
            <Route
              key="not-found"
              path="*"
              render={() => (
                <ContentError isNotFound>
                  {match.params.id && (
                    <Link
                      to={`/templates/workflow_job_template/${match.params.id}/details`}
                    >
                      {i18n._(`View Template Details`)}
                    </Link>
                  )}
                </ContentError>
              )}
            />
          </Switch>
        </Card>
      </PageSection>
    );
  }
}

export { WorkflowJobTemplate as _WorkflowJobTemplate };
export default withI18n()(withRouter(WorkflowJobTemplate));
