import React, { Component } from 'react';
import { I18n, i18nMark } from '@lingui/react';
import { Trans, t } from '@lingui/macro';
import {
  Switch,
  Route,
  withRouter,
  Redirect
} from 'react-router-dom';
import {
  Card,
  CardBody,
  CardHeader,
  PageSection
} from '@patternfly/react-core';

import OrganizationDetail from './OrganizationDetail';
import OrganizationEdit from './OrganizationEdit';
import OrganizationNotifications from './OrganizationNotifications';
import Tabs from '../../../../components/Tabs/Tabs';
import Tab from '../../../../components/Tabs/Tab';

class Organization extends Component {
  constructor (props) {
    super(props);

    this.state = {
      organization: null,
      error: false,
      loading: true,
    };

    this.fetchOrganization = this.fetchOrganization.bind(this);
  }

  componentDidMount () {
    this.fetchOrganization();
  }

  async componentDidUpdate (prevProps) {
    const { location } = this.props;
    if (location !== prevProps.location) {
      await this.fetchOrganization();
    }
  }

  async fetchOrganization () {
    const {
      api,
      match,
      setBreadcrumb
    } = this.props;
    try {
      const { data } = await api.getOrganizationDetails(+match.params.id);
      this.setState({ organization: data });
      setBreadcrumb(data);
    } catch (error) {
      this.setState({ error: true });
    } finally {
      this.setState({ loading: false });
    }
  }

  render () {
    const {
      location,
      match,
      api,
      history
    } = this.props;

    const {
      organization,
      error,
      loading
    } = this.state;

    const tabElements = [
      { name: i18nMark('Details'), link: `${match.url}/details` },
      { name: i18nMark('Access'), link: `${match.url}/access` },
      { name: i18nMark('Teams'), link: `${match.url}/teams` },
      { name: i18nMark('Notifications'), link: `${match.url}/notifications` },
    ];

    let cardHeader = (
      <CardHeader>
        <I18n>
          {({ i18n }) => (
            <Tabs
              labelText={i18n._(t`Organization detail tabs`)}
              closeButton={{ link: '/organizations', text: i18nMark('Close') }}
            >
              {tabElements.map(tabElement => (
                <Tab
                  key={tabElement.name}
                  link={tabElement.link}
                  replace
                >
                  {tabElement.name}
                </Tab>
              ))}
            </Tabs>
          )}
        </I18n>
      </CardHeader>
    );

    if (location.pathname.endsWith('edit')) {
      cardHeader = null;
    }

    return (
      <PageSection>
        <Card>
          { cardHeader }
          <Switch>
            <Redirect
              from="/organizations/:id"
              to="/organizations/:id/details"
              exact
            />
            {organization && (
              <Route
                path="/organizations/:id/edit"
                render={() => (
                  <OrganizationEdit
                    api={api}
                    match={match}
                    organization={organization}
                  />
                )}
              />
            )}
            {organization && (
              <Route
                path="/organizations/:id/details"
                render={() => (
                  <OrganizationDetail
                    api={api}
                    match={match}
                    organization={organization}
                  />
                )}
              />
            )}
            <Route
              path="/organizations/:id/access"
              render={() => <CardBody><h1><Trans>Access</Trans></h1></CardBody>}
            />
            <Route
              path="/organizations/:id/teams"
              render={() => <CardBody><h1><Trans>Teams</Trans></h1></CardBody>}
            />
            <Route
              path="/organizations/:id/notifications"
              render={() => (
                <OrganizationNotifications
                  api={api}
                  match={match}
                  location={location}
                  history={history}
                />
              )}
            />
          </Switch>
          {error ? 'error!' : ''}
          {loading ? 'loading...' : ''}
        </Card>
      </PageSection>
    );
  }
}

export default withRouter(Organization);
