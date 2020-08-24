import 'styled-components/macro';
import React from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  UrlFormField,
  ScmCredentialFormField,
  ScmTypeOptions,
} from './SharedFields';

const ArchiveSubForm = ({
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
          {i18n._(t`Example URLs for Remote Archive Source Control include:`)}
          <ul css={{ margin: '10px 0 10px 20px' }}>
            <li>https://github.com/username/project/archive/v0.0.1.tar.gz</li>
            <li>https://github.com/username/project/archive/v0.0.2.zip</li>
          </ul>
        </span>
      }
    />
    <ScmCredentialFormField
      credential={credential}
      onCredentialSelection={onCredentialSelection}
    />
    <ScmTypeOptions scmUpdateOnLaunch={scmUpdateOnLaunch} />
  </>
);

export default withI18n()(ArchiveSubForm);
