import React, { useState } from 'react';

import { t } from '@lingui/macro';
import { Link, useHistory } from 'react-router-dom';
import { Button, Tooltip } from '@patternfly/react-core';
import { Tr, Td } from '@patternfly/react-table';
import { RocketIcon } from '@patternfly/react-icons';

import { SystemJobTemplatesAPI } from 'api';
import AlertModal from 'components/AlertModal';
import ErrorDetail from 'components/ErrorDetail';
import { ActionsTd, ActionItem } from 'components/PaginatedTable';
import LaunchManagementPrompt from './LaunchManagementPrompt';

function ManagementJobListItem({
  onLaunchError,
  isPrompted,
  isSuperUser,
  id,
  jobType,
  name,
  description,
}) {
  const detailsUrl = `/management_jobs/${id}`;

  const history = useHistory();
  const [isLaunchLoading, setIsLaunchLoading] = useState(false);

  const [isManagementPromptOpen, setIsManagementPromptOpen] = useState(false);
  const [isManagementPromptLoading, setIsManagementPromptLoading] =
    useState(false);
  const [managementPromptError, setManagementPromptError] = useState(null);
  const handleManagementPromptClick = () => setIsManagementPromptOpen(true);
  const handleManagementPromptClose = () => setIsManagementPromptOpen(false);

  const handleManagementPromptConfirm = async (days) => {
    setIsManagementPromptLoading(true);
    try {
      const { data } = await SystemJobTemplatesAPI.launch(id, {
        extra_vars: { days },
      });
      history.push(`/jobs/management/${data.id}/output`);
    } catch (error) {
      setManagementPromptError(error);
    } finally {
      setIsManagementPromptLoading(false);
    }
  };

  const handleLaunch = async () => {
    setIsLaunchLoading(true);
    try {
      const { data } = await SystemJobTemplatesAPI.launch(id);
      history.push(`/jobs/management/${data.id}/output`);
    } catch (error) {
      onLaunchError(error);
    } finally {
      setIsLaunchLoading(false);
    }
  };

  const rowId = `mgmt-jobs-row-${jobType ? jobType.replace('_', '-') : ''}`;
  return (
    <>
      <Tr id={rowId} ouiaId={rowId}>
        <Td />
        <Td dataLabel={t`Name`}>
          <Link to={`${detailsUrl}`}>
            <b>{name}</b>
          </Link>
        </Td>
        <Td dataLabel={t`Description`}>{description}</Td>
        <ActionsTd dataLabel={t`Actions`}>
          <ActionItem visible={isSuperUser} tooltip={t`Launch Management Job`}>
            {isSuperUser ? (
              <>
                {isPrompted ? (
                  <LaunchManagementPrompt
                    isOpen={isManagementPromptOpen}
                    isLoading={isManagementPromptLoading}
                    onClick={handleManagementPromptClick}
                    onClose={handleManagementPromptClose}
                    onConfirm={handleManagementPromptConfirm}
                    defaultDays={30}
                  />
                ) : (
                  <Tooltip content={t`Launch management job`} position="top">
                    <Button
                      ouiaId={`${id}-launch-button`}
                      aria-label={t`Launch management job`}
                      variant="plain"
                      onClick={handleLaunch}
                      isDisabled={isLaunchLoading}
                    >
                      <RocketIcon />
                    </Button>
                  </Tooltip>
                )}{' '}
              </>
            ) : null}
          </ActionItem>
        </ActionsTd>
      </Tr>
      {managementPromptError && (
        <AlertModal
          isOpen={managementPromptError}
          variant="danger"
          onClose={() => setManagementPromptError(null)}
          title={t`Management job launch error`}
          label={t`Management job launch error`}
        >
          <ErrorDetail error={managementPromptError} />
        </AlertModal>
      )}
    </>
  );
}

export default ManagementJobListItem;
