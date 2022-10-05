import 'styled-components/macro';
import React from 'react';
import { t } from '@lingui/macro';
import FormField from 'components/FormField';
import getDocsBaseUrl from 'util/getDocsBaseUrl';
import { useConfig } from 'contexts/Config';

import {
  UrlFormField,
  BranchFormField,
  ScmCredentialFormField,
  ScmTypeOptions,
} from './SharedFields';
import getProjectHelpStrings from '../Project.helptext';

const GitSubForm = ({ credentialTypeId, scmUpdateOnLaunch }) => {
  const docsURL = `${getDocsBaseUrl(
    useConfig()
  )}/html/userguide/projects.html#manage-playbooks-using-source-control`;
  const projectHelpStrings = getProjectHelpStrings();

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
        tooltip={projectHelpStrings.sourceControlRefspec(docsURL)}
      />
      <ScmCredentialFormField credentialTypeId={credentialTypeId} />
      <ScmTypeOptions scmUpdateOnLaunch={scmUpdateOnLaunch} />
    </>
  );
};

export default GitSubForm;
