/* eslint-disable react/no-unescaped-entities */
import React from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import PropTypes from 'prop-types';
import { useField } from 'formik';
import { Form, FormGroup, Switch, Checkbox } from '@patternfly/react-core';
import styled from 'styled-components';

import { BrandName } from '../../variables';
import AnsibleSelect from '../AnsibleSelect';
import FormField, { FieldTooltip } from '../FormField';
import { VariablesField } from '../CodeMirrorInput';
import {
  FormColumnLayout,
  FormFullWidthLayout,
  FormCheckboxLayout,
} from '../FormLayout';
import { required } from '../../util/validators';

const TooltipWrapper = styled.div`
  text-align: left;
`;

// Setting BrandName to a variable here is necessary to get the jest tests
// passing.  Attempting to use BrandName in the template literal results
// in failing tests.
const brandName = BrandName;

function CredentialStep({ i18n, verbosityOptions, moduleOptions }) {
  const [module_nameField, module_nameMeta, module_nameHelpers] = useField({
    name: 'module_name',
    validate: required(null, i18n),
  });

  const [variablesField] = useField('extra_vars');
  const [diff_modeField, , diff_modeHelpers] = useField('diff_mode');
  const [become_enabledField, , become_enabledHelpers] = useField(
    'become_enabled'
  );
  const [verbosityField, verbosityMeta, verbosityHelpers] = useField({
    name: 'verbosity',
    validate: required(null, i18n),
  });
  return (
    <Form>
      <FormColumnLayout>
        <FormFullWidthLayout>
          <FormGroup
            fieldId="module_name"
            label={i18n._(t`Module`)}
            isRequired
            helperTextInvalid={module_nameMeta.error}
            validated={
              !module_nameMeta.touched || !module_nameMeta.error
                ? 'default'
                : 'error'
            }
            labelIcon={
              <FieldTooltip
                content={i18n._(
                  t`These are the modules that ${brandName} supports running commands against.`
                )}
              />
            }
          >
            <AnsibleSelect
              {...module_nameField}
              isValid={!module_nameMeta.touched || !module_nameMeta.error}
              id="module_name"
              data={moduleOptions || []}
              onChange={(event, value) => {
                module_nameHelpers.setValue(value);
              }}
            />
          </FormGroup>
          <FormField
            id="module_args"
            name="module_args"
            type="text"
            label={i18n._(t`Arguments`)}
            validate={required(null, i18n)}
            isRequired={
              module_nameField.value === 'command' ||
              module_nameField.value === 'shell'
            }
            tooltip={
              module_nameField.value ? (
                <>
                  {i18n._(
                    t`These arguments are used with the specified module. You can find information about the ${module_nameField.value} by clicking `
                  )}
                  <a
                    href={`https://docs.ansible.com/ansible/latest/modules/${module_nameField.value}_module.html`}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {' '}
                    {i18n._(t`here.`)}
                  </a>
                </>
              ) : (
                i18n._(t`These arguments are used with the specified module.`)
              )
            }
          />
          <FormGroup
            fieldId="verbosity"
            label={i18n._(t`Verbosity`)}
            isRequired
            validated={
              !verbosityMeta.touched || !verbosityMeta.error
                ? 'default'
                : 'error'
            }
            helperTextInvalid={verbosityMeta.error}
            labelIcon={
              <FieldTooltip
                content={i18n._(
                  t`These are the verbosity levels for standard out of the command run that are supported.`
                )}
              />
            }
          >
            <AnsibleSelect
              {...verbosityField}
              isValid={!verbosityMeta.touched || !verbosityMeta.error}
              id="verbosity"
              data={verbosityOptions || []}
              onChange={(event, value) => {
                verbosityHelpers.setValue(parseInt(value, 10));
              }}
            />
          </FormGroup>
          <FormField
            id="limit"
            name="limit"
            type="text"
            label={i18n._(t`Limit`)}
            tooltip={
              <span>
                {i18n._(
                  t`The pattern used to target hosts in the inventory. Leaving the field blank, all, and * will all target all hosts in the inventory. You can find more information about Ansible's host patterns`
                )}{' '}
                <a
                  href="https://docs.ansible.com/ansible/latest/user_guide/intro_patterns.html"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {i18n._(`here`)}
                </a>
              </span>
            }
          />
          <FormField
            id="template-forks"
            name="forks"
            type="number"
            min="0"
            label={i18n._(t`Forks`)}
            tooltip={
              <span>
                {i18n._(
                  t`The number of parallel or simultaneous processes to use while executing the playbook. Inputting no value will use the default value from the ansible configuration file.  You can find more information`
                )}{' '}
                <a
                  href="https://docs.ansible.com/ansible/latest/installation_guide/intro_configuration.html#the-ansible-configuration-file"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {i18n._(t`here.`)}
                </a>
              </span>
            }
          />
          <FormColumnLayout>
            <FormGroup
              label={i18n._(t`Show changes`)}
              labelIcon={
                <FieldTooltip
                  content={i18n._(
                    t`If enabled, show the changes made by Ansible tasks, where supported. This is equivalent to Ansible’s --diff mode.`
                  )}
                />
              }
            >
              <Switch
                css="display: inline-flex;"
                id="diff_mode"
                label={i18n._(t`On`)}
                labelOff={i18n._(t`Off`)}
                isChecked={diff_modeField.value}
                onChange={() => {
                  diff_modeHelpers.setValue(!diff_modeField.value);
                }}
                aria-label={i18n._(t`toggle changes`)}
              />
            </FormGroup>
            <FormGroup name="become_enabled" fieldId="become_enabled">
              <FormCheckboxLayout>
                <Checkbox
                  aria-label={i18n._(t`Enable privilege escalation`)}
                  label={
                    <span>
                      {i18n._(t`Enable privilege escalation`)}
                      &nbsp;
                      <FieldTooltip
                        content={
                          <p>
                            {i18n._(t`Enables creation of a provisioning
                              callback URL. Using the URL a host can contact ${brandName}
                              and request a configuration update using this job
                              template`)}
                            &nbsp;
                            <code>--become </code>
                            {i18n._(t`option to the`)} &nbsp;
                            <code>ansible </code>
                            {i18n._(t`command`)}
                          </p>
                        }
                      />
                    </span>
                  }
                  id="become_enabled"
                  isChecked={become_enabledField.value}
                  onChange={checked => {
                    become_enabledHelpers.setValue(checked);
                  }}
                />
              </FormCheckboxLayout>
            </FormGroup>
          </FormColumnLayout>

          <VariablesField
            css="margin: 20px 0"
            id="extra_vars"
            name="extra_vars"
            value={JSON.stringify(variablesField.value)}
            rows={4}
            labelIcon
            tooltip={
              <TooltipWrapper>
                <p>
                  {i18n._(
                    t`Pass extra command line changes. There are two ansible command line parameters: `
                  )}
                  <br />
                  <code>-e</code>, <code>--extra-vars </code>
                  <br />
                  {i18n._(t`Provide key/value pairs using either
                  YAML or JSON.`)}
                </p>
                JSON:
                <br />
                <code>
                  <pre>
                    {'{'}
                    {'\n  '}"somevar": "somevalue",
                    {'\n  '}"password": "magic"
                    {'\n'}
                    {'}'}
                  </pre>
                </code>
                YAML:
                <br />
                <code>
                  <pre>
                    ---
                    {'\n'}somevar: somevalue
                    {'\n'}password: magic
                  </pre>
                </code>
              </TooltipWrapper>
            }
            label={i18n._(t`Extra variables`)}
          />
        </FormFullWidthLayout>
      </FormColumnLayout>
    </Form>
  );
}

CredentialStep.propTypes = {
  moduleOptions: PropTypes.arrayOf(PropTypes.object).isRequired,
  verbosityOptions: PropTypes.arrayOf(PropTypes.object).isRequired,
};

export default withI18n()(CredentialStep);
