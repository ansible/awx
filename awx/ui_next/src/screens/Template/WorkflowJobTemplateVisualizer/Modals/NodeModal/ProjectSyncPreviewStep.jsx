import React from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Title } from '@patternfly/react-core';
import { DetailList, Detail } from '@components/DetailList';
import HorizontalSeparator from '@components/HorizontalSeparator';

function ProjectPreviewStep({ i18n, project, linkType }) {
  let linkTypeValue;

  switch (linkType) {
    case 'success':
      linkTypeValue = i18n._(t`On Success`);
      break;
    case 'failure':
      linkTypeValue = i18n._(t`On Failure`);
      break;
    case 'always':
      linkTypeValue = i18n._(t`Always`);
      break;
    default:
      break;
  }

  return (
    <div>
      <Title headingLevel="h1" size="xl">
        {i18n._(t`Project Sync Node`)}
      </Title>
      <HorizontalSeparator />
      <DetailList gutter="sm">
        <Detail label={i18n._(t`Name`)} value={project.name} />
        <Detail label={i18n._(t`Run`)} value={linkTypeValue} />
      </DetailList>
    </div>
  );
}

export default withI18n()(ProjectPreviewStep);
