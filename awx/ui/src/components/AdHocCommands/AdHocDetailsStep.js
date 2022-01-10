/* eslint-disable react/no-unescaped-entities */
import React from 'react';
import { t } from '@lingui/macro';
import PropTypes from 'prop-types';
import { useField } from 'formik';
import { Form, FormGroup, Switch, Checkbox } from '@patternfly/react-core';
import styled from 'styled-components';
import { required } from 'util/validators';
import useBrandName from 'hooks/useBrandName';
import AnsibleSelect from '../AnsibleSelect';
import FormField from '../FormField';
import { VariablesField } from '../CodeEditor';
import {
  FormColumnLayout,
  FormFullWidthLayout,
  FormCheckboxLayout,
} from '../FormLayout';
import Popover from '../Popover';

const TooltipWrapper = styled.div`
  text-align: left;
`;

function AdHocDetailsStep({ verbosityOptions, moduleOptions }) {
  const brandName = useBrandName();
  const [moduleNameField, moduleNameMeta, moduleNameHelpers] = useField({
    name: 'module_name',
    validate: required(null),
  });

  const [variablesField] = useField('extra_vars');
  const [diffModeField, , diffModeHelpers] = useField('diff_mode');
  const [becomeEnabledField, , becomeEnabledHelpers] =
    useField('become_enabled');
  const [verbosityField, verbosityMeta, verbosityHelpers] = useField({
    name: 'verbosity',
    validate: required(null),
  });

  const argumentsRequired =
    moduleNameField.value === 'command' || moduleNameField.value === 'shell';
  const [argumentsField, argumentsMeta, argumentsHelpers] = useField({
    name: 'module_args',
    validate: argumentsRequired && required(null),
  });

  const isValid = argumentsRequired
    ? (!argumentsMeta.error || !argumentsMeta.touched) && argumentsField.value
    : true;

  return (
    <Form>
      <FormColumnLayout>
        <FormFullWidthLayout>
          <FormGroup
            fieldId="module_name"
            aria-label={t`select module`}
            label={t`Module`}
            isRequired
            helperTextInvalid={moduleNameMeta.error}
            validated={
              !moduleNameMeta.touched || !moduleNameMeta.error
                ? 'default'
                : 'error'
            }
            labelIcon={
              <Popover
                content={t`These are the modules that ${brandName} supports running commands against.`}
              />
            }
          >
            <AnsibleSelect
              {...moduleNameField}
              placeHolder={t`Select a module`}
              isValid={!moduleNameMeta.touched || !moduleNameMeta.error}
              id="module_name"
              data={[
                {
                  value: '',
                  key: '',
                  label: t`Choose a module`,
                  isDisabled: true,
                },
                ...moduleOptions.map((value) => ({
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
            aria-label={t`Arguments`}
            type="text"
            label={t`Arguments`}
            validated={isValid ? 'default' : 'error'}
            onBlur={() => argumentsHelpers.setTouched(true)}
            isRequired={argumentsRequired}
            tooltip={
              moduleNameField.value ? (
                <>
                  {t`These arguments are used with the specified module. You can find information about ${moduleNameField.value} by clicking `}
                  <a
                    href={`https://docs.ansible.com/ansible/latest/modules/${moduleNameField.value}_module.html`}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {' '}
                    {t`here.`}
                  </a>
                </>
              ) : (
                t`These arguments are used with the specified module.`
              )
            }
          />
          <FormGroup
            fieldId="verbosity"
            aria-label={t`select verbosity`}
            label={t`Verbosity`}
            isRequired
            validated={
              !verbosityMeta.touched || !verbosityMeta.error
                ? 'default'
                : 'error'
            }
            helperTextInvalid={verbosityMeta.error}
            labelIcon={
              <Popover
                content={t`These are the verbosity levels for standard out of the command run that are supported.`}
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
            label={t`Limit`}
            aria-label={t`Limit`}
            tooltip={
              <span>
                {t`The pattern used to target hosts in the inventory. Leaving the field blank, all, and * will all target all hosts in the inventory. You can find more information about Ansible's host patterns`}{' '}
                <a
                  href="https://docs.ansible.com/ansible/latest/user_guide/intro_patterns.html"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {t`here`}
                </a>
              </span>
            }
          />
          <FormField
            id="template-forks"
            name="forks"
            type="number"
            min="0"
            label={t`Forks`}
            aria-label={t`Forks`}
            tooltip={
              <span>
                {t`The number of parallel or simultaneous processes to use while executing the playbook. Inputting no value will use the default value from the ansible configuration file.  You can find more information`}{' '}
                <a
                  href="https://docs.ansible.com/ansible/latest/installation_guide/intro_configuration.html#the-ansible-configuration-file"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {t`here.`}
                </a>
              </span>
            }
          />
          <FormColumnLayout>
            <FormGroup
              label={t`Show changes`}
              aria-label={t`Show changes`}
              labelIcon={
                <Popover
                  content={t`If enabled, show the changes made by Ansible tasks, where supported. This is equivalent to Ansible’s --diff mode.`}
                />
              }
            >
              <Switch
                css="display: inline-flex;"
                id="diff_mode"
                label={t`On`}
                labelOff={t`Off`}
                isChecked={diffModeField.value}
                onChange={() => {
                  diffModeHelpers.setValue(!diffModeField.value);
                }}
                ouiaId="diff-mode-switch"
                aria-label={t`toggle changes`}
              />
            </FormGroup>
            <FormGroup name="become_enabled" fieldId="become_enabled">
              <FormCheckboxLayout>
                <Checkbox
                  aria-label={t`Enable privilege escalation`}
                  label={
                    <span>
                      {t`Enable privilege escalation`}
                      &nbsp;
                      <Popover
                        content={
                          <p>
                            {t`Enables creation of a provisioning
                              callback URL. Using the URL a host can contact ${brandName}
                              and request a configuration update using this job
                              template`}
                            &nbsp;
                            <code>--become </code>
                            {t`option to the`} &nbsp;
                            <code>ansible </code>
                            {t`command`}
                          </p>
                        }
                      />
                    </span>
                  }
                  id="become_enabled"
                  ouiaId="become_enabled"
                  isChecked={becomeEnabledField.value}
                  onChange={(checked) => {
                    becomeEnabledHelpers.setValue(checked);
                  }}
                />
              </FormCheckboxLayout>
            </FormGroup>
          </FormColumnLayout>

          <VariablesField
            id="extra_vars"
            name="extra_vars"
            value={JSON.stringify(variablesField.value)}
            rows={4}
            labelIcon
            tooltip={
              <TooltipWrapper>
                <p>
                  {t`Pass extra command line changes. There are two ansible command line parameters: `}
                  <br />
                  <code>-e</code>, <code>--extra-vars </code>
                  <br />
                  {t`Provide key/value pairs using either
                  YAML or JSON.`}
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
            label={t`Extra variables`}
            aria-label={t`Extra variables`}
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

export default AdHocDetailsStep;
