import React, { Component } from 'react';
import { t } from '@lingui/macro';
import { withI18n } from '@lingui/react';
import { Card, CardHeader, PageSection } from '@patternfly/react-core';
import { Switch, Route, Redirect, withRouter } from 'react-router-dom';

import CardCloseButton from '@components/CardCloseButton';
import ContentError from '@components/ContentError';
import RoutedTabs from '@components/RoutedTabs';
import JobTemplateDetail from './JobTemplateDetail';
import { JobTemplatesAPI } from '@api';

class Template extends Component {
  constructor (props) {
    super(props);
    this.state = {
      hasContentError: false,
      hasContentLoading: true,
      template: {}
    };
    this.readTemplate = this.readTemplate.bind(this);
  }

  componentDidMount () {
    this.readTemplate();
  }

  async readTemplate () {
    const { setBreadcrumb, match } = this.props;
    const { id } = match.params;
    try {
      const { data } = await JobTemplatesAPI.readDetail(id);
      setBreadcrumb(data);
      this.setState({ template: data });
    } catch {
      this.setState({ hasContentError: true });
    } finally {
      this.setState({ hasContentLoading: false });
    }
  }

  render () {
    const { match, i18n, history } = this.props;
    const { hasContentLoading, template, hasContentError } = this.state;

    const tabsArray = [
      { name: i18n._(t`Details`), link: `${match.url}/details`, id: 0 },
      { name: i18n._(t`Access`), link: '/home', id: 1 },
      { name: i18n._(t`Notifications`), link: '/home', id: 2 },
      { name: i18n._(t`Schedules`), link: '/home', id: 3 },
      { name: i18n._(t`Completed Jobs`), link: '/home', id: 4 },
      { name: i18n._(t`Survey`), link: '/home', id: 5 }
    ];
    const cardHeader = (hasContentLoading ? null
      : (
        <CardHeader style={{ padding: 0 }}>
          <RoutedTabs
            history={history}
            tabsArray={tabsArray}
          />
          <CardCloseButton linkTo="/templates" />
        </CardHeader>
      )
    );

    if (!hasContentLoading && hasContentError) {
      return (
        <PageSection>
          <Card className="awx-c-card">
            <ContentError />
          </Card>
        </PageSection>
      );
    }
    return (
      <PageSection>
        <Card className="awx-c-card">
          { cardHeader }
          <Switch>
            <Redirect
              from="/templates/:templateType/:id"
              to="/templates/:templateType/:id/details"
              exact
            />
            {template && (
              <Route
                path="/templates/:templateType/:id/details"
                render={() => (
                  <JobTemplateDetail
                    match={match}
                    hasTemplateLoading={hasContentLoading}
                    template={template}
                  />
                )}
              />
            )}
          </Switch>
        </Card>
      </PageSection>
    );
  }
}
export { Template as _Template };
export default withI18n()(withRouter(Template));
