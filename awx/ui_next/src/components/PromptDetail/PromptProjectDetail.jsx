import React from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { List, ListItem } from '@patternfly/react-core';
import { Link } from 'react-router-dom';
import { Config } from '../../contexts/Config';

import { Detail, DeletedDetail } from '../DetailList';
import CredentialChip from '../CredentialChip';
import { toTitleCase } from '../../util/strings';

function PromptProjectDetail({ i18n, resource }) {
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

  return (
    <>
      {summary_fields?.organization ? (
        <Detail
          label={i18n._(t`Organization`)}
          value={
            <Link
              to={`/organizations/${summary_fields.organization.id}/details`}
            >
              {summary_fields?.organization.name}
            </Link>
          }
        />
      ) : (
        <DeletedDetail label={i18n._(t`Organization`)} />
      )}
      <Detail
        label={i18n._(t`Source Control Type`)}
        value={scm_type === '' ? i18n._(t`Manual`) : toTitleCase(scm_type)}
      />
      <Detail label={i18n._(t`Source Control URL`)} value={scm_url} />
      <Detail label={i18n._(t`Source Control Branch`)} value={scm_branch} />
      <Detail label={i18n._(t`Source Control Refspec`)} value={scm_refspec} />
      {summary_fields?.credential?.id && (
        <Detail
          label={i18n._(t`Source Control Credential`)}
          value={
            <CredentialChip
              key={resource.summary_fields.credential.id}
              credential={resource.summary_fields.credential}
              isReadOnly
            />
          }
        />
      )}
      {optionsList && <Detail label={i18n._(t`Options`)} value={optionsList} />}
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
    </>
  );
}

export default withI18n()(PromptProjectDetail);
