import React, { useState } from 'react';
import { Link, useHistory } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Project } from '@types';
import { Config } from '@contexts/Config';

import { Button, List, ListItem } from '@patternfly/react-core';
import AlertModal from '@components/AlertModal';
import { CardBody, CardActionsRow } from '@components/Card';
import ContentLoading from '@components/ContentLoading';
import DeleteButton from '@components/DeleteButton';
import { DetailList, Detail, UserDateDetail } from '@components/DetailList';
import ErrorDetail from '@components/ErrorDetail';
import CredentialChip from '@components/CredentialChip';
import { ProjectsAPI } from '@api';
import { toTitleCase } from '@util/strings';

function ProjectDetail({ project, i18n }) {
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
  const [deletionError, setDeletionError] = useState(null);
  const [hasContentLoading, setHasContentLoading] = useState(false);
  const history = useHistory();

  const handleDelete = async () => {
    setHasContentLoading(true);
    try {
      await ProjectsAPI.destroy(id);
      history.push(`/projects`);
    } catch (error) {
      setDeletionError(error);
    }
    setHasContentLoading(false);
  };

  let optionsList = '';
  if (
    scm_clean ||
    scm_delete_on_update ||
    scm_update_on_launch ||
    allow_override
  ) {
    optionsList = (
      <List>
        {scm_clean && <ListItem>{i18n._(t`Clean`)}</ListItem>}
        {scm_delete_on_update && (
          <ListItem>{i18n._(t`Delete on Update`)}</ListItem>
        )}
        {scm_update_on_launch && (
          <ListItem>{i18n._(t`Update Revision on Launch`)}</ListItem>
        )}
        {allow_override && (
          <ListItem>{i18n._(t`Allow Branch Override`)}</ListItem>
        )}
      </List>
    );
  }

  if (hasContentLoading) {
    return <ContentLoading />;
  }

  return (
    <CardBody>
      <DetailList gutter="sm">
        <Detail
          label={i18n._(t`Name`)}
          value={name}
          dataCy="project-detail-name"
        />
        <Detail label={i18n._(t`Description`)} value={description} />
        {summary_fields.organization && (
          <Detail
            label={i18n._(t`Organization`)}
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
          label={i18n._(t`SCM Type`)}
          value={
            scm_type === '' ? i18n._(t`Manual`) : toTitleCase(project.scm_type)
          }
        />
        <Detail label={i18n._(t`SCM URL`)} value={scm_url} />
        <Detail label={i18n._(t`SCM Branch`)} value={scm_branch} />
        <Detail label={i18n._(t`SCM Refspec`)} value={scm_refspec} />
        {summary_fields.credential && (
          <Detail
            label={i18n._(t`SCM Credential`)}
            value={
              <CredentialChip
                key={summary_fields.credential.id}
                credential={summary_fields.credential}
                isReadOnly
              />
            }
          />
        )}
        {optionsList && (
          <Detail label={i18n._(t`Options`)} value={optionsList} />
        )}
        <Detail
          label={i18n._(t`Cache Timeout`)}
          value={`${scm_update_cache_timeout} ${i18n._(t`Seconds`)}`}
        />
        <Detail
          label={i18n._(t`Ansible Environment`)}
          value={custom_virtualenv}
        />
        <Config>
          {({ project_base_dir }) => (
            <Detail
              label={i18n._(t`Project Base Path`)}
              value={project_base_dir}
            />
          )}
        </Config>
        <Detail label={i18n._(t`Playbook Directory`)} value={local_path} />
        <UserDateDetail
          label={i18n._(t`Created`)}
          date={created}
          user={summary_fields.created_by}
        />
        <UserDateDetail
          label={i18n._(t`Last Modified`)}
          date={modified}
          user={summary_fields.modified_by}
        />
      </DetailList>
      <CardActionsRow>
        {summary_fields.user_capabilities &&
          summary_fields.user_capabilities.edit && (
            <Button
              aria-label={i18n._(t`edit`)}
              component={Link}
              to={`/projects/${id}/edit`}
            >
              {i18n._(t`Edit`)}
            </Button>
          )}
        {summary_fields.user_capabilities &&
          summary_fields.user_capabilities.delete && (
            <DeleteButton
              name={name}
              modalTitle={i18n._(t`Delete Project`)}
              onConfirm={handleDelete}
            >
              {i18n._(t`Delete`)}
            </DeleteButton>
          )}
      </CardActionsRow>
      {/* Update delete modal to show dependencies https://github.com/ansible/awx/issues/5546 */}
      {deletionError && (
        <AlertModal
          isOpen={deletionError}
          variant="error"
          title={i18n._(t`Error!`)}
          onClose={() => setDeletionError(null)}
        >
          {i18n._(t`Failed to delete project.`)}
          <ErrorDetail error={deletionError} />
        </AlertModal>
      )}
    </CardBody>
  );
}

ProjectDetail.propTypes = {
  project: Project.isRequired,
};

export default withI18n()(ProjectDetail);
