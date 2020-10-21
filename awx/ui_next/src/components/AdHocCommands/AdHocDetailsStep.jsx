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
import FormField from '../FormField';
import { VariablesField } from '../CodeMirrorInput';
import {
  FormColumnLayout,
  FormFullWidthLayout,
  FormCheckboxLayout,
} from '../FormLayout';
import Popover from '../Popover';
import { required } from '../../util/validators';

const TooltipWrapper = styled.div`
  text-align: left;
`;

// Setting BrandName to a variable here is necessary to get the jest tests
// passing.  Attempting to use BrandName in the template literal results
// in failing tests.
const brandName = BrandName;

function AdHocDetailsStep({ i18n, verbosityOptions, moduleOptions }) {
  const [moduleNameField, moduleNameMeta, moduleNameHelpers] = useField({
    name: 'module_name',
    validate: required(null, i18n),
  });

  const [variablesField] = useField('extra_vars');
  const [diffModeField, , diffModeHelpers] = useField('diff_mode');
  const [becomeEnabledField, , becomeEnabledHelpers] = useField(
    'become_enabled'
  );
  const [verbosityField, verbosityMeta, verbosityHelpers] = useField({
    name: 'verbosity',
    validate: required(null, i18n),
  });

  const argumentsRequired =
    moduleNameField.value === 'command' || moduleNameField.value === 'shell';
  const [, argumentsMeta, argumentsHelpers] = useField({
    name: 'module_args',
    validate: argumentsRequired && required(null, i18n),
  });

  const isValid = !argumentsMeta.error || !argumentsMeta.touched;

  return (
    <Form>
      <FormColumnLayout>
        <FormFullWidthLayout>
          <FormGroup
            fieldId="module_name"
            aria-label={i18n._(t`select module`)}
            label={i18n._(t`Module`)}
            isRequired
            helperTextInvalid={moduleNameMeta.error}
            validated={
              !moduleNameMeta.touched || !moduleNameMeta.error
                ? 'default'
                : 'error'
            }
            labelIcon={
              <Popover
                content={i18n._(
                  t`These are the modules that ${brandName} supports running commands against.`
                )}
              />
            }
          >
            <AnsibleSelect
              {...moduleNameField}
              placeHolder={i18n._(t`Select a module`)}
              isValid={!moduleNameMeta.touched || !moduleNameMeta.error}
              id="module_name"
              data={[
                {
                  value: '',
                  key: '',
                  label: i18n._(t`Choose a module`),
                  isDisabled: true,
                },
                ...moduleOptions.map(value => ({
                  value: value[0],
                  label: value[0],
                  key: value[0],
                })),
              ]}
              onChange={(event, value) => {
                if (value !== 'command' && value !== 'shell') {
                  argumentsHelpers.setTouched(false);
                }
                moduleNameHelpers.setValue(value);
              }}
            />
          </FormGroup>
          <FormField
            id="module_args"
            name="module_args"
            aria-label={i18n._(t`Arguments`)}
            type="text"
            label={i18n._(t`Arguments`)}
            validated={isValid ? 'default' : 'error'}
            onBlur={() => argumentsHelpers.setTouched(true)}
            isRequired={
              moduleNameField.value === 'command' ||
              moduleNameField.value === 'shell'
            }
            tooltip={
              moduleNameField.value ? (
                <>
                  {i18n._(
                    t`These arguments are used with the specified module. You can find information about ${moduleNameField.value} by clicking `
                  )}
                  <a
                    href={`https://docs.ansible.com/ansible/latest/modules/${moduleNameField.value}_module.html`}
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
            aria-label={i18n._(t`select verbosity`)}
            label={i18n._(t`Verbosity`)}
            isRequired
            validated={
              !verbosityMeta.touched || !verbosityMeta.error
                ? 'default'
                : 'error'
            }
            helperTextInvalid={verbosityMeta.error}
            labelIcon={
              <Popover
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
            aria-label={i18n._(t`Limit`)}
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
                  {i18n._(t`here`)}
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
            aria-label={i18n._(t`Forks`)}
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
              aria-label={i18n._(t`Show changes`)}
              labelIcon={
                <Popover
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
                isChecked={diffModeField.value}
                onChange={() => {
                  diffModeHelpers.setValue(!diffModeField.value);
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
                      <Popover
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
                  isChecked={becomeEnabledField.value}
                  onChange={checked => {
                    becomeEnabledHelpers.setValue(checked);
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
            aria-label={i18n._(t`Extra variables`)}
          />
        </FormFullWidthLayout>
      </FormColumnLayout>
    </Form>
  );
}

AdHocDetailsStep.propTypes = {
  moduleOptions: PropTypes.arrayOf(PropTypes.array).isRequired,
  verbosityOptions: PropTypes.arrayOf(PropTypes.object).isRequired,
};

export default withI18n()(AdHocDetailsStep);
