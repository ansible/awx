import React, { Component, Fragment } from 'react';
import { Route, withRouter, Switch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import Breadcrumbs from '@components/Breadcrumbs/Breadcrumbs';
import Job from './Job';
import JobList from './JobList/JobList';
import { JOB_TYPE_URLS } from './constants';

class Jobs extends Component {
  constructor(props) {
    super(props);

    const { i18n } = props;

    this.state = {
      breadcrumbConfig: {
        '/jobs': i18n._(t`Jobs`),
      },
    };
  }

  setBreadcrumbConfig = job => {
    const { i18n } = this.props;

    if (!job) {
      return;
    }

    const type = JOB_TYPE_URLS[job.type];
    const breadcrumbConfig = {
      '/jobs': i18n._(t`Jobs`),
      [`/jobs/${type}/${job.id}`]: `${job.name}`,
      [`/jobs/${type}/${job.id}/details`]: i18n._(t`Details`),
      [`/jobs/${type}/${job.id}/output`]: i18n._(t`Output`),
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
          <Route
            exact
            path={match.path}
            render={() => (
              <JobList
                history={history}
                location={location}
                setBreadcrumb={this.setBreadcrumbConfig}
              />
            )}
          />
          <Route
            path={`${match.path}/:type/:id`}
            render={() => (
              <Job
                history={history}
                location={location}
                setBreadcrumb={this.setBreadcrumbConfig}
              />
            )}
          />
        </Switch>
      </Fragment>
    );
  }
}

export { Jobs as _Jobs };
export default withI18n()(withRouter(Jobs));
