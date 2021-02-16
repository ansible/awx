import React, { Fragment, useState } from 'react';
import { withRouter } from 'react-router-dom';
import { number, shape } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import AlertModal from '../AlertModal';
import ErrorDetail from '../ErrorDetail';
import {
  AdHocCommandsAPI,
  InventorySourcesAPI,
  JobsAPI,
  JobTemplatesAPI,
  ProjectsAPI,
  WorkflowJobsAPI,
  WorkflowJobTemplatesAPI,
} from '../../api';
import LaunchPrompt from '../LaunchPrompt';

function canLaunchWithoutPrompt(launchData) {
  return (
    launchData.can_start_without_user_input &&
    !launchData.ask_inventory_on_launch &&
    !launchData.ask_variables_on_launch &&
    !launchData.ask_limit_on_launch &&
    !launchData.ask_scm_branch_on_launch &&
    !launchData.survey_enabled &&
    (!launchData.passwords_needed_to_start ||
      launchData.passwords_needed_to_start.length === 0) &&
    (!launchData.variables_needed_to_start ||
      launchData.variables_needed_to_start.length === 0)
  );
}

function LaunchButton({ resource, i18n, children, history }) {
  const [showLaunchPrompt, setShowLaunchPrompt] = useState(false);
  const [launchConfig, setLaunchConfig] = useState(null);
  const [surveyConfig, setSurveyConfig] = useState(null);
  const [error, setError] = useState(null);
  const handleLaunch = async () => {
    const readLaunch =
      resource.type === 'workflow_job_template'
        ? WorkflowJobTemplatesAPI.readLaunch(resource.id)
        : JobTemplatesAPI.readLaunch(resource.id);
    const readSurvey =
      resource.type === 'workflow_job_template'
        ? WorkflowJobTemplatesAPI.readSurvey(resource.id)
        : JobTemplatesAPI.readSurvey(resource.id);
    try {
      const { data: launch } = await readLaunch;
      setLaunchConfig(launch);

      if (launch.survey_enabled) {
        const { data } = await readSurvey;

        setSurveyConfig(data);
      }

      if (canLaunchWithoutPrompt(launch)) {
        launchWithParams({});
      } else {
        setShowLaunchPrompt(true);
      }
    } catch (err) {
      setError(err);
    }
  };

  const launchWithParams = async params => {
    try {
      let jobPromise;

      if (resource.type === 'job_template') {
        jobPromise = JobTemplatesAPI.launch(resource.id, params || {});
      } else if (resource.type === 'workflow_job_template') {
        jobPromise = WorkflowJobTemplatesAPI.launch(resource.id, params || {});
      } else if (resource.type === 'job') {
        jobPromise = JobsAPI.relaunch(resource.id, params || {});
      } else if (resource.type === 'workflow_job') {
        jobPromise = WorkflowJobsAPI.relaunch(resource.id, params || {});
      }

      const { data: job } = await jobPromise;
      history.push(`/jobs/${job.id}/output`);
    } catch (launchError) {
      setError(launchError);
    }
  };

  const handleRelaunch = async params => {
    let readRelaunch;
    let relaunch;

    if (resource.type === 'inventory_update') {
      // We'll need to handle the scenario where the src no longer exists
      readRelaunch = InventorySourcesAPI.readLaunchUpdate(
        resource.inventory_source
      );
    } else if (resource.type === 'project_update') {
      // We'll need to handle the scenario where the project no longer exists
      readRelaunch = ProjectsAPI.readLaunchUpdate(resource.project);
    } else if (resource.type === 'workflow_job') {
      readRelaunch = WorkflowJobsAPI.readRelaunch(resource.id);
    } else if (resource.type === 'ad_hoc_command') {
      readRelaunch = AdHocCommandsAPI.readRelaunch(resource.id);
    } else if (resource.type === 'job') {
      readRelaunch = JobsAPI.readRelaunch(resource.id);
    }

    try {
      const { data: relaunchConfig } = await readRelaunch;
      setLaunchConfig(relaunchConfig);
      if (
        !relaunchConfig.passwords_needed_to_start ||
        relaunchConfig.passwords_needed_to_start.length === 0
      ) {
        if (resource.type === 'inventory_update') {
          relaunch = InventorySourcesAPI.launchUpdate(
            resource.inventory_source
          );
        } else if (resource.type === 'project_update') {
          relaunch = ProjectsAPI.launchUpdate(resource.project);
        } else if (resource.type === 'workflow_job') {
          relaunch = WorkflowJobsAPI.relaunch(resource.id);
        } else if (resource.type === 'ad_hoc_command') {
          relaunch = AdHocCommandsAPI.relaunch(resource.id);
        } else if (resource.type === 'job') {
          relaunch = JobsAPI.relaunch(resource.id, params || {});
        }
        const { data: job } = await relaunch;
        history.push(`/jobs/${job.id}/output`);
      } else {
        setShowLaunchPrompt(true);
      }
    } catch (err) {
      setError(err);
    }
  };

  return (
    <Fragment>
      {children({
        handleLaunch,
        handleRelaunch,
      })}
      {error && (
        <AlertModal
          isOpen={error}
          variant="error"
          title={i18n._(t`Error!`)}
          onClose={() => setError(null)}
        >
          {i18n._(t`Failed to launch job.`)}
          <ErrorDetail error={error} />
        </AlertModal>
      )}
      {showLaunchPrompt && (
        <LaunchPrompt
          launchConfig={launchConfig}
          surveyConfig={surveyConfig}
          resource={resource}
          onLaunch={launchWithParams}
          onCancel={() => setShowLaunchPrompt(false)}
        />
      )}
    </Fragment>
  );
}

LaunchButton.propTypes = {
  resource: shape({
    id: number.isRequired,
  }).isRequired,
};

export default withI18n()(withRouter(LaunchButton));
