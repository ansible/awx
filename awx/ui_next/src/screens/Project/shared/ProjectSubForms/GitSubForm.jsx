import 'styled-components/macro';
import React from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import FormField from '../../../../components/FormField';
import {
  UrlFormField,
  BranchFormField,
  ScmCredentialFormField,
  ScmTypeOptions,
} from './SharedFields';

const GitSubForm = ({
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
          {i18n._(t`Example URLs for GIT Source Control include:`)}
          <ul css="margin: 10px 0 10px 20px">
            <li>https://github.com/ansible/ansible.git</li>
            <li>git@github.com:ansible/ansible.git</li>
            <li>git://servername.example.com/ansible.git</li>
          </ul>
          {i18n._(t`Note: When using SSH protocol for GitHub or
            Bitbucket, enter an SSH key only, do not enter a username
            (other than git). Additionally, GitHub and Bitbucket do
            not support password authentication when using SSH. GIT
            read only protocol (git://) does not use username or
            password information.`)}
        </span>
      }
    />
    <BranchFormField
      i18n={i18n}
      label={i18n._(t`Source Control Branch/Tag/Commit`)}
    />
    <FormField
      id="project-scm-refspec"
      label={i18n._(t`Source Control Refspec`)}
      name="scm_refspec"
      type="text"
      tooltipMaxWidth="400px"
      tooltip={
        <span>
          {i18n._(t`A refspec to fetch (passed to the Ansible git
            module). This parameter allows access to references via
            the branch field not otherwise available.`)}
          <br />
          <br />
          {i18n._(t`Note: This field assumes the remote name is "origin".`)}
          <br />
          <br />
          {i18n._(t`Examples include:`)}
          <ul css={{ margin: '10px 0 10px 20px' }}>
            <li>refs/*:refs/remotes/origin/*</li>
            <li>refs/pull/62/head:refs/remotes/origin/pull/62/head</li>
          </ul>
          {i18n._(t`The first fetches all references. The second
            fetches the Github pull request number 62, in this example
            the branch needs to be "pull/62/head".`)}
          <br />
          <br />
          {i18n._(t`For more information, refer to the`)}{' '}
          <a
            target="_blank"
            rel="noopener noreferrer"
            href="https://docs.ansible.com/ansible-tower/latest/html/userguide/projects.html#manage-playbooks-using-source-control"
          >
            {i18n._(t`Ansible Tower Documentation.`)}
          </a>
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

export default withI18n()(GitSubForm);
