import React, { Component, Fragment } from 'react';
import { Route, withRouter, Switch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import { Config } from '@contexts/Config';
import Breadcrumbs from '@components/Breadcrumbs/Breadcrumbs';

import HostList from './HostList';
import HostAdd from './HostAdd';
import Host from './Host';

class Hosts extends Component {
  constructor(props) {
    super(props);

    const { i18n } = props;

    this.state = {
      breadcrumbConfig: {
        '/hosts': i18n._(t`Hosts`),
        '/hosts/add': i18n._(t`Create New Host`),
      },
    };
  }

  setBreadcrumbConfig = host => {
    const { i18n } = this.props;

    if (!host) {
      return;
    }

    const breadcrumbConfig = {
      '/hosts': i18n._(t`Hosts`),
      '/hosts/add': i18n._(t`Create New Host`),
      [`/hosts/${host.id}`]: `${host.name}`,
      [`/hosts/${host.id}/edit`]: i18n._(t`Edit Details`),
      [`/hosts/${host.id}/details`]: i18n._(t`Details`),
      [`/hosts/${host.id}/facts`]: i18n._(t`Facts`),
      [`/hosts/${host.id}/groups`]: i18n._(t`Groups`),
      [`/hosts/${host.id}/completed_jobs`]: i18n._(t`Completed Jobs`),
    };

    this.setState({ breadcrumbConfig });
  };

  render() {
    const { match, history, location } = this.props;
    const { breadcrumbConfig } = this.state;

    return (
      <Fragment>
        <Breadcrumbs breadcrumbConfig={breadcrumbConfig} />
        <Switch>
          <Route path={`${match.path}/add`} render={() => <HostAdd />} />
          <Route
            path={`${match.path}/:id`}
            render={() => (
              <Config>
                {({ me }) => (
                  <Host
                    history={history}
                    location={location}
                    setBreadcrumb={this.setBreadcrumbConfig}
                    me={me || {}}
                  />
                )}
              </Config>
            )}
          />
          <Route path={`${match.path}`} render={() => <HostList />} />
        </Switch>
      </Fragment>
    );
  }
}

export { Hosts as _Hosts };
export default withI18n()(withRouter(Hosts));
