import 'styled-components/macro';
import React from 'react';
import ProjectHelpTextStrings from '../Project.helptext';

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
  const projectHelpText = ProjectHelpTextStrings();
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
