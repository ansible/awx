import React from 'react';
import { Link, withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import styled from 'styled-components';
import { Project } from '@types';
import { formatDateString } from '@util/dates';
import { Button, CardBody, List, ListItem } from '@patternfly/react-core';
import { DetailList, Detail } from '@components/DetailList';
import { CredentialChip } from '@components/Chip';

const ActionButtonWrapper = styled.div`
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
  & > :not(:first-child) {
    margin-left: 20px;
  }
`;

function ProjectDetail({ project, i18n }) {
  const {
    allow_override,
    created,
    custom_virtualenv,
    description,
    id,
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

  let createdBy = '';
  if (created) {
    if (summary_fields.created_by && summary_fields.created_by.username) {
      createdBy = i18n._(
        t`${formatDateString(created)} by ${summary_fields.created_by.username}`
      );
    } else {
      createdBy = formatDateString(created);
    }
  }

  let modifiedBy = '';
  if (modified) {
    if (summary_fields.modified_by && summary_fields.modified_by.username) {
      modifiedBy = i18n._(
        t`${formatDateString(modified)} by ${
          summary_fields.modified_by.username
        }`
      );
    } else {
      modifiedBy = formatDateString(modified);
    }
  }

  return (
    <CardBody css="padding-top: 20px">
      <DetailList gutter="sm">
        <Detail label={i18n._(t`Name`)} value={name} />
        <Detail label={i18n._(t`Description`)} value={description} />
        {summary_fields.organization && (
          <Detail
            label={i18n._(t`Organization`)}
            value={summary_fields.organization.name}
          />
        )}
        <Detail label={i18n._(t`SCM Type`)} value={scm_type} />
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
        {/* TODO: Link to user in users */}
        <Detail label={i18n._(t`Created`)} value={createdBy} />
        {/* TODO: Link to user in users */}
        <Detail label={i18n._(t`Last Modified`)} value={modifiedBy} />
      </DetailList>
      <ActionButtonWrapper>
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
      </ActionButtonWrapper>
    </CardBody>
  );
}

ProjectDetail.propTypes = {
  project: Project.isRequired,
};

export default withI18n()(withRouter(ProjectDetail));
