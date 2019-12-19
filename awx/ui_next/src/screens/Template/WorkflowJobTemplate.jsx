import React, { Component } from 'react';
import { t } from '@lingui/macro';
import { withI18n } from '@lingui/react';
import { Card, PageSection } from '@patternfly/react-core';
import { Switch, Route, Redirect, withRouter, Link } from 'react-router-dom';
import { TabbedCardHeader } from '@components/Card';
import AppendBody from '@components/AppendBody';
import CardCloseButton from '@components/CardCloseButton';
import ContentError from '@components/ContentError';
import FullPage from '@components/FullPage';
import RoutedTabs from '@components/RoutedTabs';
import { WorkflowJobTemplatesAPI } from '@api';
import WorkflowJobTemplateDetail from './WorkflowJobTemplateDetail';
import { Visualizer } from './WorkflowJobTemplateVisualizer';

class WorkflowJobTemplate extends Component {
  constructor(props) {
    super(props);

    this.state = {
      contentError: null,
      hasContentLoading: true,
      template: null,
    };
    this.loadTemplate = this.loadTemplate.bind(this);
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

    this.setState({ contentError: null, hasContentLoading: true });
    try {
      const { data } = await WorkflowJobTemplatesAPI.readDetail(id);
      setBreadcrumb(data);
      this.setState({ template: data });
    } catch (err) {
      this.setState({ contentError: err });
    } finally {
      this.setState({ hasContentLoading: false });
    }
  }

  render() {
    const { history, i18n, location, match } = this.props;
    const { contentError, hasContentLoading, template } = this.state;

    const tabsArray = [
      { name: i18n._(t`Details`), link: `${match.url}/details` },
      { name: i18n._(t`Visualizer`), link: `${match.url}/visualizer` },
    ];

    tabsArray.forEach((tab, n) => {
      tab.id = n;
    });

    let cardHeader = hasContentLoading ? null : (
      <TabbedCardHeader>
        <RoutedTabs history={history} tabsArray={tabsArray} />
        <CardCloseButton linkTo="/templates" />
      </TabbedCardHeader>
    );

    if (location.pathname.endsWith('edit')) {
      cardHeader = null;
    }

    if (!hasContentLoading && contentError) {
      return (
        <PageSection>
          <Card className="awx-c-card">
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
        <Card className="awx-c-card">
          {cardHeader}
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
                    match={match}
                    hasTemplateLoading={hasContentLoading}
                    template={template}
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
            <Route
              key="not-found"
              path="*"
              render={() =>
                !hasContentLoading && (
                  <ContentError isNotFound>
                    {match.params.id && (
                      <Link
                        to={`/templates/workflow_job_template/${match.params.id}/details`}
                      >
                        {i18n._(`View Template Details`)}
                      </Link>
                    )}
                  </ContentError>
                )
              }
            />
          </Switch>
        </Card>
      </PageSection>
    );
  }
}

export { WorkflowJobTemplate as _WorkflowJobTemplate };
export default withI18n()(withRouter(WorkflowJobTemplate));
