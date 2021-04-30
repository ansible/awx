import React from 'react';

import { Trans, t } from '@lingui/macro';
import { useField } from 'formik';
import { Flex, FormGroup, TextArea } from '@patternfly/react-core';
import { required } from '../../../../util/validators';
import { useConfig } from '../../../../contexts/Config';
import { CheckboxField } from '../../../../components/FormField';

function EulaStep() {
  const { eula, me } = useConfig();
  const [, meta] = useField('eula');
  const isValid = !(meta.touched && meta.error);
  return (
    <Flex
      spaceItems={{ default: 'spaceItemsMd' }}
      direction={{ default: 'column' }}
    >
      <b>
        <Trans>Agree to the end user license agreement and click submit.</Trans>
      </b>
      <FormGroup
        fieldId="eula"
        label={t`End User License Agreement`}
        validated={isValid ? 'default' : 'error'}
        helperTextInvalid={meta.error}
        isRequired
      >
        <TextArea
          id="eula-container"
          style={{ minHeight: '200px' }}
          resizeOrientation="vertical"
          isReadOnly
        >
          {eula}
        </TextArea>
        <CheckboxField
          name="eula"
          aria-label={t`Agree to end user license agreement`}
          label={t`I agree to the End User License Agreement`}
          id="eula"
          isDisabled={!me.is_superuser}
          validate={required(
            t`Please agree to End User License Agreement before proceeding.`
          )}
        />
      </FormGroup>
    </Flex>
  );
}
export default EulaStep;
