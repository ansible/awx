import React, { Component, Fragment } from 'react';
import { Route, withRouter, Switch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import Breadcrumbs from '../../components/Breadcrumbs/Breadcrumbs';
import { Job } from '.';

class Jobs extends Component {
  constructor (props) {
    super(props);

    const { i18n } = props;

    this.state = {
      breadcrumbConfig: {
        '/jobs': i18n._(t`Jobs`)
      }
    };
  }

  setBreadcrumbConfig = (job) => {
    const { i18n } = this.props;

    if (!job) {
      return;
    }

    const breadcrumbConfig = {
      '/jobs': i18n._(t`Jobs`),
      [`/jobs/${job.id}`]: `${job.name}`,
      [`/jobs/${job.id}/details`]: i18n._(t`Details`),
      [`/jobs/${job.id}/output`]: i18n._(t`Output`)
    };

    this.setState({ breadcrumbConfig });
  }

  render () {
    const { match, history, location } = this.props;
    const { breadcrumbConfig } = this.state;

    return (
      <Fragment>
        <Breadcrumbs
          breadcrumbConfig={breadcrumbConfig}
        />
        <Switch>
          <Route
            path={`${match.path}/:id`}
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

export default withI18n()(withRouter(Jobs));
