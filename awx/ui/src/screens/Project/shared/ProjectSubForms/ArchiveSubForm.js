import 'styled-components/macro';
import React from 'react';
import getProjectHelpText from '../Project.helptext';

import {
  UrlFormField,
  ScmCredentialFormField,
  ScmTypeOptions,
} from './SharedFields';

const ArchiveSubForm = ({
  credential,
  onCredentialSelection,
  scmUpdateOnLaunch,
}) => {
  const projectHelpText = getProjectHelpText();
  return (
    <>
      <UrlFormField tooltip={projectHelpText.archiveUrl} />
      <ScmCredentialFormField
        credential={credential}
        onCredentialSelection={onCredentialSelection}
      />
      <ScmTypeOptions scmUpdateOnLaunch={scmUpdateOnLaunch} />
    </>
  );
};

export default ArchiveSubForm;
