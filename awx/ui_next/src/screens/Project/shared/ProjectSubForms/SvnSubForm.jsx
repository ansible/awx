import 'styled-components/macro';
import React from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  UrlFormField,
  BranchFormField,
  ScmCredentialFormField,
  ScmTypeOptions,
} from './SharedFields';

const SvnSubForm = ({
  i18n,
  credential,
  onCredentialSelection,
  scmUpdateOnLaunch,
}) => (
  <>
    <UrlFormField
      i18n={i18n}
      tooltip={
        <span>
          {i18n._(t`Example URLs for Subversion Source Control include:`)}
          <ul css={{ margin: '10px 0 10px 20px' }}>
            <li>https://github.com/ansible/ansible</li>
            <li>svn://servername.example.com/path</li>
            <li>svn+ssh://servername.example.com/path</li>
          </ul>
        </span>
      }
    />
    <BranchFormField i18n={i18n} label={i18n._(t`Revision #`)} />
    <ScmCredentialFormField
      credential={credential}
      onCredentialSelection={onCredentialSelection}
    />
    <ScmTypeOptions scmUpdateOnLaunch={scmUpdateOnLaunch} />
  </>
);

export default withI18n()(SvnSubForm);
