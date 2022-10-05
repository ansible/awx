import 'styled-components/macro';
import React from 'react';
import getProjectHelpText from '../Project.helptext';

import {
  UrlFormField,
  ScmCredentialFormField,
  ScmTypeOptions,
} from './SharedFields';

const ArchiveSubForm = ({ credentialTypeId, scmUpdateOnLaunch }) => {
  const projectHelpText = getProjectHelpText();
  return (
    <>
      <UrlFormField tooltip={projectHelpText.archiveUrl} />
      <ScmCredentialFormField credentialTypeId={credentialTypeId} />
      <ScmTypeOptions scmUpdateOnLaunch={scmUpdateOnLaunch} />
    </>
  );
};

export default ArchiveSubForm;
