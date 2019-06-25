import React, { Component } from 'react';
import { t } from '@lingui/macro';
import { withI18n } from '@lingui/react';
import {
  Card,
  CardHeader,
  PageSection,
} from '@patternfly/react-core';
import {
  Switch,
  Route,
  Redirect,
  withRouter,
} from 'react-router-dom';
import CardCloseButton from '@components/CardCloseButton';
import ContentError from '@components/ContentError';
import RoutedTabs from '@components/RoutedTabs';
import JobTemplateDetail from './JobTemplateDetail';
import { JobTemplatesAPI } from '@api';
import TemplateEdit from './TemplateEdit';

class Template extends Component {
  constructor (props) {
    super(props);

    this.state = {
      hasContentError: false,
      hasContentLoading: true,
      template: null,
      actions: null,
    };
    this.loadTemplate = this.loadTemplate.bind(this);
  }

  async componentDidMount () {
    await this.loadTemplate();
  }

  async componentDidUpdate (prevProps) {
    const { location } = this.props;
    if (location !== prevProps.location) {
      await this.loadTemplate();
    }
  }

  async loadTemplate () {
    const { actions: cachedActions } = this.state;
    const { setBreadcrumb, match } = this.props;
    const { id } = match.params;

    let optionsPromise;
    if (cachedActions) {
      optionsPromise = Promise.resolve({ data: { actions: cachedActions } });
    } else {
      optionsPromise = JobTemplatesAPI.readOptions();
    }

    const promises = Promise.all([
      JobTemplatesAPI.readDetail(id),
      optionsPromise
    ]);

    this.setState({ hasContentError: false, hasContentLoading: true });
    try {
      const [{ data }, { data: { actions } }] = await promises;
      setBreadcrumb(data);
      this.setState({
        template: data,
        actions
      });
    } catch {
      this.setState({ hasContentError: true });
    } finally {
      this.setState({ hasContentLoading: false });
    }
  }

  render () {
    const {
      history,
      i18n,
      location,
      match,
    } = this.props;

    const {
      actions,
      hasContentError,
      hasContentLoading,
      template
    } = this.state;

    const canAdd = actions && Object.prototype.hasOwnProperty.call(actions, 'POST');

    const tabsArray = [
      { name: i18n._(t`Details`), link: `${match.url}/details`, id: 0 },
      { name: i18n._(t`Access`), link: '/home', id: 1 },
      { name: i18n._(t`Notifications`), link: '/home', id: 2 },
      { name: i18n._(t`Schedules`), link: '/home', id: 3 },
      { name: i18n._(t`Completed Jobs`), link: '/home', id: 4 },
      { name: i18n._(t`Survey`), link: '/home', id: 5 }
    ];

    let cardHeader = (hasContentLoading ? null
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

    if (location.pathname.endsWith('edit')) {
      cardHeader = null;
    }

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
            {template && (
              <Route
                path="/templates/:templateType/:id/edit"
                render={() => (
                  <TemplateEdit
                    template={template}
                    hasPermissions={canAdd}
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
