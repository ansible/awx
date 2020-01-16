import React, { useEffect, useState } from 'react';
import { withI18n } from '@lingui/react';
import { Trans } from '@lingui/macro';
import { t } from '@lingui/macro';
import { ProjectsAPI } from '@api';
import { Config } from '@contexts/Config';
import ContentError from '@components/ContentError';
import ContentLoading from '@components/ContentLoading';
import { DetailList, Detail } from '@components/DetailList';
import { CredentialChip } from '@components/Chip';
import { toTitleCase } from '@util/strings';

function ProjectSyncDetails({ i18n, node }) {
  const [project, setProject] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [noReadAccess, setNoReadAccess] = useState(false);
  const [contentError, setContentError] = useState(null);

  useEffect(() => {
    async function fetchProject() {
      try {
        const { data } = await ProjectsAPI.readDetail(
          node.unifiedJobTemplate.id
        );
        setProject(data);
      } catch (err) {
        if (err.response.status === 403) {
          setNoReadAccess(true);
        } else {
          setContentError(err);
        }
      } finally {
        setIsLoading(false);
      }
    }
    fetchProject();
  }, []);

  if (isLoading) {
    return <ContentLoading />;
  }

  if (contentError) {
    return <ContentError error={contentError} />;
  }

  if (noReadAccess) {
    return (
      <>
        <p>
          <Trans>
            Your account does not have read access to this project so the
            displayed details will be limited.
          </Trans>
        </p>
        <br />
        <DetailList gutter="sm">
          <Detail
            label={i18n._(t`Node Type`)}
            value={i18n._(t`Project Sync`)}
          />
          <Detail
            label={i18n._(t`Name`)}
            value={node.unifiedJobTemplate.name}
          />
          <Detail
            label={i18n._(t`Description`)}
            value={node.unifiedJobTemplate.description}
          />
        </DetailList>
      </>
    );
  }

  const {
    custom_virtualenv,
    description,
    local_path,
    name,
    scm_branch,
    scm_refspec,
    scm_type,
    scm_update_cache_timeout,
    scm_url,
    summary_fields,
  } = project;

  return (
    <DetailList gutter="sm">
      <Detail label={i18n._(t`Node Type`)} value={i18n._(t`Project Sync`)} />
      <Detail label={i18n._(t`Name`)} value={name} />
      <Detail label={i18n._(t`Description`)} value={description} />
      {summary_fields.organization && (
        <Detail
          label={i18n._(t`Organization`)}
          value={summary_fields.organization.name}
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
    </DetailList>
  );
}

export default withI18n()(ProjectSyncDetails);
