import React, { Fragment } from 'react';
import { withRouter } from 'react-router-dom';
import { number, shape } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import AlertModal from '@components/AlertModal';
import ErrorDetail from '@components/ErrorDetail';
import {
  AdHocCommandsAPI,
  InventorySourcesAPI,
  JobsAPI,
  JobTemplatesAPI,
  ProjectsAPI,
  WorkflowJobsAPI,
  WorkflowJobTemplatesAPI,
} from '@api';

function canLaunchWithoutPrompt(launchData) {
  return (
    launchData.can_start_without_user_input &&
    !launchData.ask_inventory_on_launch &&
    !launchData.ask_variables_on_launch &&
    !launchData.ask_limit_on_launch &&
    !launchData.ask_scm_branch_on_launch &&
    !launchData.survey_enabled &&
    launchData.variables_needed_to_start.length === 0
  );
}

class LaunchButton extends React.Component {
  static propTypes = {
    resource: shape({
      id: number.isRequired,
    }).isRequired,
  };

  constructor(props) {
    super(props);

    this.state = {
      launchError: null,
      promptError: false,
    };

    this.handleLaunch = this.handleLaunch.bind(this);
    this.handleRelaunch = this.handleRelaunch.bind(this);
    this.handleLaunchErrorClose = this.handleLaunchErrorClose.bind(this);
    this.handlePromptErrorClose = this.handlePromptErrorClose.bind(this);
  }

  handleLaunchErrorClose() {
    this.setState({ launchError: null });
  }

  handlePromptErrorClose() {
    this.setState({ promptError: false });
  }

  async handleLaunch() {
    const { history, resource } = this.props;

    const readLaunch =
      resource.type === 'workflow_job_template'
        ? WorkflowJobTemplatesAPI.readLaunch(resource.id)
        : JobTemplatesAPI.readLaunch(resource.id);

    const launchJob =
      resource.type === 'workflow_job_template'
        ? WorkflowJobTemplatesAPI.launch(resource.id)
        : JobTemplatesAPI.launch(resource.id);

    try {
      const { data: launchConfig } = await readLaunch;

      if (canLaunchWithoutPrompt(launchConfig)) {
        const { data: job } = await launchJob;

        history.push(
          `/${
            resource.type === 'workflow_job_template' ? 'jobs/workflow' : 'jobs'
          }/${job.id}/output`
        );
      } else {
        this.setState({ promptError: true });
      }
    } catch (err) {
      this.setState({ launchError: err });
    }
  }

  async handleRelaunch() {
    const { history, resource } = this.props;

    let readRelaunch;
    let relaunch;

    if (resource.type === 'inventory_update') {
      // We'll need to handle the scenario where the src no longer exists
      readRelaunch = InventorySourcesAPI.readLaunchUpdate(
        resource.inventory_source
      );
      relaunch = InventorySourcesAPI.launchUpdate(resource.inventory_source);
    } else if (resource.type === 'project_update') {
      // We'll need to handle the scenario where the project no longer exists
      readRelaunch = ProjectsAPI.readLaunchUpdate(resource.project);
      relaunch = ProjectsAPI.launchUpdate(resource.project);
    } else if (resource.type === 'workflow_job') {
      readRelaunch = WorkflowJobsAPI.readRelaunch(resource.id);
      relaunch = WorkflowJobsAPI.relaunch(resource.id);
    } else if (resource.type === 'ad_hoc_command') {
      readRelaunch = AdHocCommandsAPI.readRelaunch(resource.id);
      relaunch = AdHocCommandsAPI.relaunch(resource.id);
    } else if (resource.type === 'job') {
      readRelaunch = JobsAPI.readRelaunch(resource.id);
      relaunch = JobsAPI.relaunch(resource.id);
    }

    try {
      const { data: relaunchConfig } = await readRelaunch;
      if (
        !relaunchConfig.passwords_needed_to_start ||
        relaunchConfig.passwords_needed_to_start.length === 0
      ) {
        const { data: job } = await relaunch;
        history.push(`/jobs/${job.id}/output`);
      } else {
        this.setState({ promptError: true });
      }
    } catch (err) {
      this.setState({ launchError: err });
    }
  }

  render() {
    const { launchError, promptError } = this.state;
    const { i18n, children } = this.props;
    return (
      <Fragment>
        {children({
          handleLaunch: this.handleLaunch,
          handleRelaunch: this.handleRelaunch,
        })}
        {launchError && (
          <AlertModal
            isOpen={launchError}
            variant="error"
            title={i18n._(t`Error!`)}
            onClose={this.handleLaunchErrorClose}
          >
            {i18n._(t`Failed to launch job.`)}
            <ErrorDetail error={launchError} />
          </AlertModal>
        )}
        {promptError && (
          <AlertModal
            isOpen={promptError}
            variant="info"
            title={i18n._(t`Attention!`)}
            onClose={this.handlePromptErrorClose}
          >
            {i18n._(
              t`Launching jobs with promptable fields is not supported at this time.`
            )}
          </AlertModal>
        )}
      </Fragment>
    );
  }
}

export default withI18n()(withRouter(LaunchButton));
