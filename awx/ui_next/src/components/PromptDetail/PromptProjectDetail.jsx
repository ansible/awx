import React from 'react';

import { t } from '@lingui/macro';
import { List, ListItem } from '@patternfly/react-core';
import { Link } from 'react-router-dom';
import { Config } from '../../contexts/Config';

import { Detail, DeletedDetail } from '../DetailList';
import CredentialChip from '../CredentialChip';
import { toTitleCase } from '../../util/strings';
import ExecutionEnvironmentDetail from '../ExecutionEnvironmentDetail';

function PromptProjectDetail({ resource }) {
  const {
    allow_override,
    custom_virtualenv,
    local_path,
    scm_branch,
    scm_clean,
    scm_delete_on_update,
    scm_refspec,
    scm_type,
    scm_update_on_launch,
    scm_update_cache_timeout,
    scm_url,
    summary_fields,
  } = resource;

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
    <>
      {summary_fields?.organization ? (
        <Detail
          label={t`Organization`}
          value={
            <Link
              to={`/organizations/${summary_fields.organization.id}/details`}
            >
              {summary_fields?.organization.name}
            </Link>
          }
        />
      ) : (
        <DeletedDetail label={t`Organization`} />
      )}
      <ExecutionEnvironmentDetail
        virtualEnvironment={custom_virtualenv}
        executionEnvironment={summary_fields?.default_environment}
        isDefaultEnvironment
      />
      <Detail
        label={t`Source Control Type`}
        value={scm_type === '' ? t`Manual` : toTitleCase(scm_type)}
      />
      <Detail label={t`Source Control URL`} value={scm_url} />
      <Detail label={t`Source Control Branch`} value={scm_branch} />
      <Detail label={t`Source Control Refspec`} value={scm_refspec} />
      {summary_fields?.credential?.id && (
        <Detail
          label={t`Source Control Credential`}
          value={
            <CredentialChip
              key={resource.summary_fields.credential.id}
              credential={resource.summary_fields.credential}
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
      <Config>
        {({ project_base_dir }) => (
          <Detail label={t`Project Base Path`} value={project_base_dir} />
        )}
      </Config>
      <Detail label={t`Playbook Directory`} value={local_path} />
    </>
  );
}

export default PromptProjectDetail;
