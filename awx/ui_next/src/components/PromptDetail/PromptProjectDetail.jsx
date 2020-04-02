import React from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Config } from '@contexts/Config';
import { List, ListItem } from '@patternfly/react-core';

import { Detail } from '@components/DetailList';
import CredentialChip from '@components/CredentialChip';
import { toTitleCase } from '@util/strings';

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
      <Detail
        label={i18n._(t`SCM Type`)}
        value={scm_type === '' ? i18n._(t`Manual`) : toTitleCase(scm_type)}
      />
      <Detail label={i18n._(t`SCM URL`)} value={scm_url} />
      <Detail label={i18n._(t`SCM Branch`)} value={scm_branch} />
      <Detail label={i18n._(t`SCM Refspec`)} value={scm_refspec} />
      {summary_fields?.credential?.id && (
        <Detail
          label={i18n._(t`SCM Credential`)}
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
