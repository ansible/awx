import React, { Component, Fragment } from 'react';
import { i18nMark } from '@lingui/react';
import {
  Switch,
  Route,
  withRouter,
} from 'react-router-dom';
import {
  PageSection
} from '@patternfly/react-core';

import OrganizationBreadcrumb from '../../components/OrganizationBreadcrumb';
import OrganizationDetail from './OrganizationDetail';
import OrganizationEdit from './OrganizationEdit';

class Organization extends Component {
  constructor (props) {
    super(props);

    let { breadcrumb: parentBreadcrumbObj, organization } = props.location.state || {};
    if (!parentBreadcrumbObj) {
      parentBreadcrumbObj = 'loading';
    }
    if (!organization) {
      organization = 'loading';
    }
    this.state = {
      parentBreadcrumbObj,
      organization,
      error: false,
      loading: false,
      mounted: false
    };

    this.fetchOrganization = this.fetchOrganization.bind(this);
  }

  componentDidMount () {
    this.setState({ mounted: true }, () => {
      const { organization } = this.state;
      if (organization === 'loading') {
        this.fetchOrganization();
      }
    });
  }

  componentWillUnmount () {
    this.setState({ mounted: false });
  }

  async fetchOrganization () {
    const { mounted } = this.state;
    const { api } = this.props;

    if (mounted) {
      this.setState({ error: false, loading: true });

      const { match } = this.props;
      const { parentBreadcrumbObj, organization } = this.state;
      try {
        const { data } = await api.getOrganizationDetails(match.params.id);
        if (organization === 'loading') {
          this.setState({ organization: data });
        }
        const { name } = data;
        if (parentBreadcrumbObj === 'loading') {
          this.setState({ parentBreadcrumbObj: [{ name: i18nMark('Organizations'), url: '/organizations' }, { name, url: match.url }] });
        }
      } catch (err) {
        this.setState({ error: true });
      } finally {
        this.setState({ loading: false });
      }
    }
  }

  render () {
    const { location, match, api, history } = this.props;
    const { parentBreadcrumbObj, organization, error, loading } = this.state;
    const params = new URLSearchParams(location.search);
    const currentTab = params.get('tab') || 'details';

    return (
      <Fragment>
        <OrganizationBreadcrumb
          parentObj={parentBreadcrumbObj}
          currentTab={currentTab}
          location={location}
          organization={organization}
        />
        <PageSection>
          <Switch>
            <Route
              path={`${match.path}/edit`}
              render={() => (
                <OrganizationEdit
                  location={location}
                  match={match}
                  parentBreadcrumbObj={parentBreadcrumbObj}
                  organization={organization}
                  params={params}
                  currentTab={currentTab}
                />
              )}
            />
            <Route
              path={`${match.path}`}
              render={() => (
                <OrganizationDetail
                  location={location}
                  match={match}
                  parentBreadcrumbObj={parentBreadcrumbObj}
                  organization={organization}
                  params={params}
                  currentTab={currentTab}
                  history={history}
                  api={api}
                />
              )}
            />
          </Switch>
          {error ? 'error!' : ''}
          {loading ? 'loading...' : ''}
        </PageSection>
      </Fragment>
    );
  }
}

export default withRouter(Organization);
