import 'styled-components/macro';
import React from 'react';
import { t } from '@lingui/macro';
import FormField from 'components/FormField';

import {
  UrlFormField,
  BranchFormField,
  ScmCredentialFormField,
  ScmTypeOptions,
} from './SharedFields';

import ProjectHelpTextStrings from '../Project.helptext';

const GitSubForm = ({
  credential,
  onCredentialSelection,
  scmUpdateOnLaunch,
}) => {
  const projectHelpStrings = ProjectHelpTextStrings();
  return (
    <>
      <UrlFormField tooltip={projectHelpStrings.githubSourceControlUrl} />
      <BranchFormField label={t`Source Control Branch/Tag/Commit`} />
      <FormField
        id="project-scm-refspec"
        label={t`Source Control Refspec`}
        name="scm_refspec"
        type="text"
        tooltipMaxWidth="400px"
        tooltip={projectHelpStrings.sourceControlRefspec}
      />
      <ScmCredentialFormField
        credential={credential}
        onCredentialSelection={onCredentialSelection}
      />
      <ScmTypeOptions scmUpdateOnLaunch={scmUpdateOnLaunch} />
    </>
  );
};

export default GitSubForm;
