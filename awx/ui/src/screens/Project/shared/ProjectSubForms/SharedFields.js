import React, { useCallback } from 'react';

import { t } from '@lingui/macro';
import { useFormikContext } from 'formik';
import { FormGroup, Title } from '@patternfly/react-core';
import CredentialLookup from 'components/Lookup/CredentialLookup';
import FormField, { CheckboxField } from 'components/FormField';
import { required } from 'util/validators';
import { FormCheckboxLayout, FormFullWidthLayout } from 'components/FormLayout';
import projectHelpStrings from '../Project.helptext';

export const UrlFormField = ({ tooltip }) => (
  <FormField
    id="project-scm-url"
    isRequired
    label={t`Source Control URL`}
    name="scm_url"
    tooltip={tooltip}
    tooltipMaxWidth="350px"
    type="text"
    validate={required(null)}
  />
);

export const BranchFormField = ({ label }) => (
  <FormField
    id="project-scm-branch"
    name="scm_branch"
    type="text"
    label={label}
    tooltip={projectHelpStrings.branchFormField}
  />
);

export const ScmCredentialFormField = ({
  credential,
  onCredentialSelection,
}) => {
  const { setFieldValue, setFieldTouched } = useFormikContext();

  const onCredentialChange = useCallback(
    (value) => {
      onCredentialSelection('scm', value);
      setFieldValue('credential', value);
      setFieldTouched('credential', true, false);
    },
    [onCredentialSelection, setFieldValue, setFieldTouched]
  );

  return (
    <CredentialLookup
      credentialTypeId={credential.typeId}
      label={t`Source Control Credential`}
      value={credential.value}
      onChange={onCredentialChange}
    />
  );
};

export const ScmTypeOptions = ({ scmUpdateOnLaunch, hideAllowOverride }) => {
  const { values } = useFormikContext();

  return (
    <FormFullWidthLayout>
      <FormGroup fieldId="project-option-checkboxes" label={t`Options`}>
        <FormCheckboxLayout>
          <CheckboxField
            id="option-scm-clean"
            name="scm_clean"
            label={t`Clean`}
            tooltip={projectHelpStrings.options.clean}
          />
          <CheckboxField
            id="option-scm-delete-on-update"
            name="scm_delete_on_update"
            label={t`Delete`}
            tooltip={projectHelpStrings.options.delete}
          />
          {values.scm_type === 'git' ? (
            <CheckboxField
              id="option-scm-track-submodules"
              name="scm_track_submodules"
              label={t`Track submodules`}
              tooltip={projectHelpStrings.options.trackSubModules}
            />
          ) : null}
          <CheckboxField
            id="option-scm-update-on-launch"
            name="scm_update_on_launch"
            label={t`Update Revision on Launch`}
            tooltip={projectHelpStrings.options.updateOnLaunch}
          />
          {!hideAllowOverride && (
            <CheckboxField
              id="option-allow-override"
              name="allow_override"
              label={t`Allow Branch Override`}
              tooltip={projectHelpStrings.options.allowBranchOverride}
            />
          )}
        </FormCheckboxLayout>
      </FormGroup>

      {scmUpdateOnLaunch && (
        <>
          <Title size="md" headingLevel="h4">
            {t`Option Details`}
          </Title>
          <FormField
            id="project-cache-timeout"
            name="scm_update_cache_timeout"
            type="number"
            min="0"
            label={t`Cache Timeout`}
            tooltip={projectHelpStrings.options.cacheTimeout}
          />
        </>
      )}
    </FormFullWidthLayout>
  );
};
