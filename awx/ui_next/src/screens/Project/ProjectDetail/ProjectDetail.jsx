import React, { useCallback } from 'react';
import { Link, useHistory } from 'react-router-dom';

import { t } from '@lingui/macro';
import { Button, List, ListItem } from '@patternfly/react-core';
import { Project } from '../../../types';
import { Config } from '../../../contexts/Config';

import AlertModal from '../../../components/AlertModal';
import { CardBody, CardActionsRow } from '../../../components/Card';
import DeleteButton from '../../../components/DeleteButton';
import {
  DetailList,
  Detail,
  UserDateDetail,
} from '../../../components/DetailList';
import ErrorDetail from '../../../components/ErrorDetail';
import ExecutionEnvironmentDetail from '../../../components/ExecutionEnvironmentDetail';
import CredentialChip from '../../../components/CredentialChip';
import { ProjectsAPI } from '../../../api';
import { toTitleCase } from '../../../util/strings';
import useRequest, { useDismissableError } from '../../../util/useRequest';
import { relatedResourceDeleteRequests } from '../../../util/getRelatedResourceDeleteDetails';
import ProjectSyncButton from '../shared/ProjectSyncButton';

function ProjectDetail({ project }) {
  const {
    allow_override,
    created,
    custom_virtualenv,
    description,
    id,
    local_path,
    modified,
    name,
    scm_branch,
    scm_clean,
    scm_delete_on_update,
    scm_refspec,
    scm_type,
    scm_update_on_launch,
    scm_update_cache_timeout,
    scm_url,
    summary_fields,
  } = project;
  const history = useHistory();

  const { request: deleteProject, isLoading, error: deleteError } = useRequest(
    useCallback(async () => {
      await ProjectsAPI.destroy(id);
      history.push(`/projects`);
    }, [id, history])
  );

  const { error, dismissError } = useDismissableError(deleteError);
  const deleteDetailsRequests = relatedResourceDeleteRequests.project(project);
  let optionsList = '';
  if (
    scm_clean ||
    scm_delete_on_update ||
    scm_update_on_launch ||
    allow_override
  ) {
    optionsList = (
      <List>
        {scm_clean && <ListItem>{t`Clean`}</ListItem>}
        {scm_delete_on_update && <ListItem>{t`Delete on Update`}</ListItem>}
        {scm_update_on_launch && (
          <ListItem>{t`Update Revision on Launch`}</ListItem>
        )}
        {allow_override && <ListItem>{t`Allow Branch Override`}</ListItem>}
      </List>
    );
  }

  return (
    <CardBody>
      <DetailList gutter="sm">
        <Detail label={t`Name`} value={name} dataCy="project-detail-name" />
        <Detail label={t`Description`} value={description} />
        {summary_fields.organization && (
          <Detail
            label={t`Organization`}
            value={
              <Link
                to={`/organizations/${summary_fields.organization.id}/details`}
              >
                {summary_fields.organization.name}
              </Link>
            }
          />
        )}
        <Detail
          label={t`Source Control Type`}
          value={scm_type === '' ? t`Manual` : toTitleCase(project.scm_type)}
        />
        <Detail label={t`Source Control URL`} value={scm_url} />
        <Detail label={t`Source Control Branch`} value={scm_branch} />
        <Detail label={t`Source Control Refspec`} value={scm_refspec} />
        {summary_fields.credential && (
          <Detail
            label={t`Source Control Credential`}
            value={
              <CredentialChip
                key={summary_fields.credential.id}
                credential={summary_fields.credential}
                isReadOnly
              />
            }
          />
        )}
        {optionsList && <Detail label={t`Options`} value={optionsList} />}
        <Detail
          label={t`Cache Timeout`}
          value={`${scm_update_cache_timeout} ${t`Seconds`}`}
        />
        <ExecutionEnvironmentDetail
          virtualEnvironment={custom_virtualenv}
          executionEnvironment={summary_fields?.default_environment}
          isDefaultEnvironment
        />
        <Config>
          {({ project_base_dir }) => (
            <Detail label={t`Project Base Path`} value={project_base_dir} />
          )}
        </Config>
        <Detail label={t`Playbook Directory`} value={local_path} />

        <UserDateDetail
          label={t`Created`}
          date={created}
          user={summary_fields.created_by}
        />
        <UserDateDetail
          label={t`Last Modified`}
          date={modified}
          user={summary_fields.modified_by}
        />
      </DetailList>
      <CardActionsRow>
        {summary_fields.user_capabilities?.edit && (
          <Button
            ouiaId="project-detail-edit-button"
            aria-label={t`edit`}
            component={Link}
            to={`/projects/${id}/edit`}
          >
            {t`Edit`}
          </Button>
        )}
        {summary_fields.user_capabilities?.start && (
          <ProjectSyncButton projectId={project.id} />
        )}
        {summary_fields.user_capabilities?.delete && (
          <DeleteButton
            name={name}
            modalTitle={t`Delete Project`}
            onConfirm={deleteProject}
            isDisabled={isLoading}
            deleteDetailsRequests={deleteDetailsRequests}
            deleteMessage={t`This project is currently being used by other resources. Are you sure you want to delete it?`}
          >
            {t`Delete`}
          </DeleteButton>
        )}
      </CardActionsRow>
      {/* Update delete modal to show dependencies https://github.com/ansible/awx/issues/5546 */}
      {error && (
        <AlertModal
          isOpen={error}
          variant="error"
          title={t`Error!`}
          onClose={dismissError}
        >
          {t`Failed to delete project.`}
          <ErrorDetail error={error} />
        </AlertModal>
      )}
    </CardBody>
  );
}

ProjectDetail.propTypes = {
  project: Project.isRequired,
};

export default ProjectDetail;
