import React from 'react';

import { t } from '@lingui/macro';
import { Flex, FormGroup, TextArea } from '@patternfly/react-core';
import { useConfig } from 'contexts/Config';

function EulaStep() {
  const { eula } = useConfig();
  return (
    <Flex
      spaceItems={{ default: 'spaceItemsMd' }}
      direction={{ default: 'column' }}
    >
      <FormGroup fieldId="eula" label={t`End User License Agreement`}>
        <TextArea
          id="eula-container"
          style={{ minHeight: '200px' }}
          resizeOrientation="vertical"
          isReadOnly
        >
          {eula}
        </TextArea>
      </FormGroup>
    </Flex>
  );
}
export default EulaStep;
