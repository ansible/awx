import React from 'react';
import { t } from '@lingui/macro';

const executionEnvironmentHelpTextStrings = () => ({
  image: (
    <span>
      {t`The full image location, including the container registry, image name, and version tag.`}
      <br />
      <br />
      {t`Examples:`}
      <ul css="margin: 10px 0 10px 20px">
        <li>
          <code>quay.io/ansible/awx-ee:latest</code>
        </li>
        <li>
          <code>repo/project/image-name:tag</code>
        </li>
      </ul>
    </span>
  ),
  registryCredential: t`Credential to authenticate with a protected container registry.`,
});

export default executionEnvironmentHelpTextStrings;
