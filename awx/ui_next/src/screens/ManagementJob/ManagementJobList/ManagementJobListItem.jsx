import React, { useState } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Link, useHistory } from 'react-router-dom';
import {
  Button,
  DataListAction as _DataListAction,
  DataListCell,
  DataListItem,
  DataListItemRow,
  DataListItemCells,
  Tooltip,
} from '@patternfly/react-core';
import { RocketIcon, PencilAltIcon } from '@patternfly/react-icons';
import styled from 'styled-components';

import { SystemJobTemplatesAPI } from '../../../api';
import AlertModal from '../../../components/AlertModal';
import ErrorDetail from '../../../components/ErrorDetail';
import LaunchManagementPrompt from './LaunchManagementPrompt';

const DataListAction = styled(_DataListAction)`
  align-items: center;
  display: grid;
  grid-gap: 16px;
  grid-template-columns: repeat(2, 40px);
`;

function ManagementJobListItem({
  i18n,
  onLaunchError,
  isConfigurable,
  isSuperUser,
  id,
  name,
  description,
  defaultDays,
}) {
  const detailsUrl = `/management_jobs/${id}/details`;
  const editUrl = `/management_jobs/${id}/edit`;
  const labelId = `mgmt-job-action-${id}`;

  const history = useHistory();
  const [isLaunchLoading, setIsLaunchLoading] = useState(false);

  const [isManagementPromptOpen, setIsManagementPromptOpen] = useState(false);
  const [isManagementPromptLoading, setIsManagementPromptLoading] = useState(
    false
  );
  const [managementPromptError, setManagementPromptError] = useState(null);
  const handleManagementPromptClick = () => setIsManagementPromptOpen(true);
  const handleManagementPromptClose = () => setIsManagementPromptOpen(false);

  const handleManagementPromptConfirm = async days => {
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

  return (
    <>
      <DataListItem key={id} id={id} aria-labelledby={labelId}>
        <DataListItemRow>
          <DataListItemCells
            dataListCells={[
              <DataListCell
                key="name"
                aria-label={i18n._(t`management job name`)}
              >
                <Link to={detailsUrl}>
                  <b>{name}</b>
                </Link>
              </DataListCell>,
              <DataListCell
                key="description"
                aria-label={i18n._(t`management job description`)}
              >
                <strong>{i18n._(t`Description:`)}</strong> {description}
              </DataListCell>,
            ]}
          />
          <DataListAction aria-labelledby={labelId} id={labelId}>
            {isSuperUser ? (
              <>
                {isConfigurable ? (
                  <>
                    <LaunchManagementPrompt
                      isOpen={isManagementPromptOpen}
                      isLoading={isManagementPromptLoading}
                      onClick={handleManagementPromptClick}
                      onClose={handleManagementPromptClose}
                      onConfirm={handleManagementPromptConfirm}
                      defaultDays={defaultDays}
                    />
                    <Tooltip
                      content={i18n._(t`Edit management job`)}
                      position="top"
                    >
                      <Button
                        aria-label={i18n._(t`Edit management job`)}
                        variant="plain"
                        component={Link}
                        to={editUrl}
                        isDisabled={isLaunchLoading}
                      >
                        <PencilAltIcon />
                      </Button>
                    </Tooltip>
                  </>
                ) : (
                  <Tooltip
                    content={i18n._(t`Launch management job`)}
                    position="top"
                  >
                    <Button
                      aria-label={i18n._(t`Launch management job`)}
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
          </DataListAction>
        </DataListItemRow>
      </DataListItem>
      {managementPromptError && (
        <>
          <AlertModal
            isOpen={managementPromptError}
            variant="danger"
            onClose={() => setManagementPromptError(null)}
            title={i18n._(t`Management job launch error`)}
            label={i18n._(t`Management job launch error`)}
          >
            <ErrorDetail error={managementPromptError} />
          </AlertModal>
        </>
      )}
    </>
  );
}

export default withI18n()(ManagementJobListItem);
