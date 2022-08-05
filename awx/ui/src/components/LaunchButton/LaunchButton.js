import React, { useState } from 'react';
import { useHistory } from 'react-router-dom';
import { number, shape } from 'prop-types';

import { t } from '@lingui/macro';

import {
  AdHocCommandsAPI,
  InventorySourcesAPI,
  JobsAPI,
  JobTemplatesAPI,
  ProjectsAPI,
  WorkflowJobsAPI,
  WorkflowJobTemplatesAPI,
} from 'api';
import AlertModal from '../AlertModal';
import ErrorDetail from '../ErrorDetail';
import LaunchPrompt from '../LaunchPrompt';

function canLaunchWithoutPrompt(launchData) {
  return (
    launchData.can_start_without_user_input &&
    !launchData.ask_inventory_on_launch &&
    !launchData.ask_variables_on_launch &&
    !launchData.ask_limit_on_launch &&
    !launchData.ask_scm_branch_on_launch &&
    !launchData.ask_execution_environment_on_launch &&
    !launchData.ask_labels_on_launch &&
    !launchData.ask_forks_on_launch &&
    !launchData.ask_job_slicing_on_launch &&
    !launchData.ask_timeout_on_launch &&
    !launchData.ask_instance_groups_on_launch &&
    !launchData.survey_enabled &&
    (!launchData.passwords_needed_to_start ||
      launchData.passwords_needed_to_start.length === 0) &&
    (!launchData.variables_needed_to_start ||
      launchData.variables_needed_to_start.length === 0)
  );
}

function LaunchButton({ resource, children }) {
  const history = useHistory();
  const [showLaunchPrompt, setShowLaunchPrompt] = useState(false);
  const [launchConfig, setLaunchConfig] = useState(null);
  const [surveyConfig, setSurveyConfig] = useState(null);
  const [isLaunching, setIsLaunching] = useState(false);
  const [error, setError] = useState(null);

  const handleLaunch = async () => {
    setIsLaunching(true);
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
        await launchWithParams({});
      } else {
        setShowLaunchPrompt(true);
      }
    } catch (err) {
      setError(err);
    } finally {
      setIsLaunching(false);
    }
  };

  const launchWithParams = async (params) => {
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
    } finally {
      setIsLaunching(false);
    }
  };

  const handleRelaunch = async (params) => {
    let readRelaunch;
    let relaunch;

    setIsLaunching(true);
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
    } finally {
      setIsLaunching(false);
    }
  };

  return (
    <>
      {children({
        handleLaunch,
        handleRelaunch,
        isLaunching,
      })}
      {error && (
        <AlertModal
          isOpen={error}
          variant="error"
          title={t`Error!`}
          onClose={() => setError(null)}
        >
          {t`Failed to launch job.`}
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
    </>
  );
}

LaunchButton.propTypes = {
  resource: shape({
    id: number.isRequired,
  }).isRequired,
};

export default LaunchButton;
