import 'styled-components/macro';
import React from 'react';

import { t } from '@lingui/macro';
import {
  UrlFormField,
  ScmCredentialFormField,
  ScmTypeOptions,
} from './SharedFields';

const ArchiveSubForm = ({
  credential,
  onCredentialSelection,
  scmUpdateOnLaunch,
}) => (
  <>
    <UrlFormField
      tooltip={
        <span>
          {t`Example URLs for Remote Archive Source Control include:`}
          <ul css={{ margin: '10px 0 10px 20px' }}>
            <li>
              <code>
                https://github.com/username/project/archive/v0.0.1.tar.gz
              </code>
            </li>
            <li>
              <code>
                https://github.com/username/project/archive/v0.0.2.zip
              </code>
            </li>
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

export default ArchiveSubForm;
