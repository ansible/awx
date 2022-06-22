import React from 'react';
import { t } from '@lingui/macro';
import { useField } from 'formik';
import { FormGroup } from '@patternfly/react-core';
import Popover from 'components/Popover';
import AnsibleSelect from 'components/AnsibleSelect';
import FieldWithPrompt from 'components/FieldWithPrompt';

const VERBOSITY = () => ({
  0: t`0 (Normal)`,
  1: t`1 (Verbose)`,
  2: t`2 (More Verbose)`,
  3: t`3 (Debug)`,
  4: t`4 (Connection Debug)`,
  5: t`5 (WinRM Debug)`,
});

function VerbositySelectField({
  fieldId,
  promptId,
  promptName,
  tooltip,
  isValid,
}) {
  const VERBOSE_OPTIONS = Object.entries(VERBOSITY()).map(([k, v]) => ({
    key: `${k}`,
    value: `${k}`,
    label: v,
  }));
  const [verbosityField, , verbosityHelpers] = useField('verbosity');
  return promptId ? (
    <FieldWithPrompt
      fieldId={fieldId}
      label={t`Verbosity`}
      promptId={promptId}
      promptName={promptName}
      tooltip={tooltip}
    >
      <AnsibleSelect id={fieldId} data={VERBOSE_OPTIONS} {...verbosityField} />
    </FieldWithPrompt>
  ) : (
    <FormGroup
      fieldId={fieldId}
      validated={isValid ? 'default' : 'error'}
      label={t`Verbosity`}
      labelIcon={<Popover content={tooltip} />}
    >
      <AnsibleSelect
        id={fieldId}
        data={VERBOSE_OPTIONS}
        {...verbosityField}
        onChange={(event, value) => verbosityHelpers.setValue(value)}
      />
    </FormGroup>
  );
}

export { VerbositySelectField, VERBOSITY };
