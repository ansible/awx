import React from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Title } from '@patternfly/react-core';
import { DetailList, Detail } from '@components/DetailList';
import HorizontalSeparator from '@components/HorizontalSeparator';

function ApprovalPreviewStep({ i18n, name, description, timeout, linkType }) {
  let linkTypeValue;

  switch (linkType) {
    case 'on_success':
      linkTypeValue = i18n._(t`On Success`);
      break;
    case 'on_failure':
      linkTypeValue = i18n._(t`On Failure`);
      break;
    case 'always':
      linkTypeValue = i18n._(t`Always`);
      break;
    default:
      break;
  }

  let timeoutValue = i18n._(t`None`);

  if (timeout) {
    const minutes = Math.floor(timeout / 60);
    const seconds = timeout - minutes * 60;
    timeoutValue = i18n._(t`${minutes}min ${seconds}sec`);
  }

  return (
    <div>
      <Title headingLevel="h1" size="xl">
        {i18n._(t`Approval Node`)}
      </Title>
      <HorizontalSeparator />
      <DetailList>
        <Detail label={i18n._(t`Name`)} value={name} />
        <Detail label={i18n._(t`Description`)} value={description} />
        <Detail label={i18n._(t`Timeout`)} value={timeoutValue} />
        <Detail label={i18n._(t`Run`)} value={linkTypeValue} />
      </DetailList>
    </div>
  );
}

export default withI18n()(ApprovalPreviewStep);
