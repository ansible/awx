import React, { Component } from 'react';
import { t } from '@lingui/macro';
import { withI18n } from '@lingui/react';
import { Card, CardHeader, PageSection } from '@patternfly/react-core';
import { Switch, Route, Redirect, withRouter, Link } from 'react-router-dom';
import CardCloseButton from '@components/CardCloseButton';
import ContentError from '@components/ContentError';
import RoutedTabs from '@components/RoutedTabs';
import JobTemplateDetail from './JobTemplateDetail';
import { JobTemplatesAPI } from '@api';
import JobTemplateEdit from './JobTemplateEdit';

class Template extends Component {
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
      const { data } = await JobTemplatesAPI.readDetail(id);
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
      { name: i18n._(t`Details`), link: `${match.url}/details`, id: 0 },
      { name: i18n._(t`Access`), link: '/home', id: 1 },
      { name: i18n._(t`Notifications`), link: '/home', id: 2 },
      { name: i18n._(t`Schedules`), link: '/home', id: 3 },
      { name: i18n._(t`Completed Jobs`), link: '/home', id: 4 },
      { name: i18n._(t`Survey`), link: '/home', id: 5 },
    ];

    let cardHeader = hasContentLoading ? null : (
      <CardHeader style={{ padding: 0 }}>
        <RoutedTabs history={history} tabsArray={tabsArray} />
        <CardCloseButton linkTo="/templates" />
      </CardHeader>
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
              from="/templates/:templateType/:id"
              to="/templates/:templateType/:id/details"
              exact
            />
            {template && [
              <Route
                key="details"
                path="/templates/:templateType/:id/details"
                render={() => (
                  <JobTemplateDetail
                    match={match}
                    hasTemplateLoading={hasContentLoading}
                    template={template}
                  />
                )}
              />,
              <Route
                key="edit"
                path="/templates/:templateType/:id/edit"
                render={() => <JobTemplateEdit template={template} />}
              />,
              <Route
                key="not-found"
                path="*"
                render={() => (
                  <ContentError isNotFound>
                    {match.params.id && (
                      <Link
                        to={`/templates/${match.params.templateType}/${match.params.id}/details`}
                      >
                        {i18n._(`View Template Details`)}
                      </Link>
                    )}
                  </ContentError>
                )}
              />,
            ]}
          </Switch>
        </Card>
      </PageSection>
    );
  }
}

export { Template as _Template };
export default withI18n()(withRouter(Template));
