import 'styled-components/macro';
import React from 'react';

import { t } from '@lingui/macro';
import {
  UrlFormField,
  BranchFormField,
  ScmCredentialFormField,
  ScmTypeOptions,
} from './SharedFields';

const SvnSubForm = ({
  credential,
  onCredentialSelection,
  scmUpdateOnLaunch,
}) => (
  <>
    <UrlFormField
      tooltip={
        <span>
          {t`Example URLs for Subversion Source Control include:`}
          <ul css={{ margin: '10px 0 10px 20px' }}>
            <li>
              <code>https://github.com/ansible/ansible</code>
            </li>
            <li>
              <code>svn://servername.example.com/path</code>
            </li>
            <li>
              <code>svn+ssh://servername.example.com/path</code>
            </li>
          </ul>
        </span>
      }
    />
    <BranchFormField label={t`Revision #`} />
    <ScmCredentialFormField
      credential={credential}
      onCredentialSelection={onCredentialSelection}
    />
    <ScmTypeOptions scmUpdateOnLaunch={scmUpdateOnLaunch} />
  </>
);

export default SvnSubForm;
