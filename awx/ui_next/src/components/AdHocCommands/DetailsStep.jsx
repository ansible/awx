/* eslint-disable react/no-unescaped-entities */
import React from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import { useField } from 'formik';
import {
  Form,
  FormGroup,
  InputGroup,
  TextInput,
  Label,
  InputGroupText,
  Switch,
  Checkbox,
} from '@patternfly/react-core';
import styled from 'styled-components';

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

function CredentialStep({
  i18n,
  verbosityOptions,
  moduleOptions,
  onLimitChange,
  limitValue,
}) {
  const [moduleField, moduleMeta, moduleHelpers] = useField({
    name: 'module_args',
    validate: required(null, i18n),
  });
  const [limitField, , limitHelpers] = useField('limit');
  const [variablesField] = useField('extra_vars');
  const [changesField, , changesHelpers] = useField('changes');
  const [escalationField, , escalationHelpers] = useField('escalation');
  const [verbosityField, verbosityMeta, verbosityHelpers] = useField({
    name: 'verbosity',
    validate: required(null, i18n),
  });

  return (
    <Form>
      <FormColumnLayout>
        <FormFullWidthLayout>
          <FormGroup
            fieldId="module"
            label={i18n._(t`Module`)}
            isRequired
            helperTextInvalid={moduleMeta.error}
            validated={
              !moduleMeta.touched || !moduleMeta.error ? 'default' : 'error'
            }
            labelIcon={
              <FieldTooltip
                content={i18n._(
                  t`These are the modules that AWX supports running commands against.`
                )}
              />
            }
          >
            <AnsibleSelect
              {...moduleField}
              isValid={!moduleMeta.touched || !moduleMeta.error}
              id="module"
              data={moduleOptions || []}
              onChange={(event, value) => {
                moduleHelpers.setValue(value);
              }}
            />
          </FormGroup>
          <FormField
            id="arguments"
            name="arguments"
            type="text"
            label={i18n._(t`Arguments`)}
            isRequired
            tooltip={i18n._(
              t`These arguments are used with the specified module.`
            )}
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
                verbosityHelpers.setValue(value);
              }}
            />
          </FormGroup>

          <FormGroup
            label={i18n._(t`Limit`)}
            labelIcon={
              <FieldTooltip
                content={
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
            }
          >
            <InputGroup>
              <InputGroupText>
                {limitField.value.map((item, index) => (
                  <Label
                    onClose={() => {
                      limitField.value.splice(index, 1);
                      limitHelpers.setValue(limitField.value);
                    }}
                  >
                    {item}
                  </Label>
                ))}
              </InputGroupText>
              <TextInput
                id="limit"
                name="limit"
                type="text"
                label={i18n._(t`Limit`)}
                value={limitValue}
                isRequired
                onChange={value => {
                  onLimitChange(value);
                }}
              />
            </InputGroup>
          </FormGroup>
          <FormField
            id="template-forks"
            name="forks"
            type="number"
            min="0"
            label={i18n._(t`Forks`)}
            tooltip={
              <span>
                {i18n._(
                  t`The number of parallel or simultaneous processes to use while executing the playbook. Inputting no value will use the default value from the `
                )}{' '}
                <a
                  href="https://docs.ansible.com/ansible/latest/installation_guide/intro_configuration.html#the-ansible-configuration-file"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {i18n._(t`ansible configuration file.`)}
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
                id="changes"
                label={i18n._(t`On`)}
                labelOff={i18n._(t`Off`)}
                isChecked={changesField.value}
                onChange={() => {
                  changesHelpers.setValue(!changesField.value);
                }}
                aria-label={i18n._(t`toggle changes`)}
              />
            </FormGroup>
            <FormGroup
              name={i18n._(t`enable privilege escalation`)}
              fieldId="escalation"
            >
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
                              callback URL. Using the URL a host can contact BRAND_NAME
                              and request a configuration update using this job
                              template`)}
                            &nbsp;
                            <code>--{i18n._(t`become`)} &nbsp;</code>
                            {i18n._(t`option to the`)} &nbsp;
                            <code>{i18n._(t`ansible`)} &nbsp;</code>
                            {i18n._(t`command`)}
                          </p>
                        }
                      />
                    </span>
                  }
                  id="escalation"
                  isChecked={escalationField.value}
                  onChange={checked => {
                    escalationHelpers.setValue(checked);
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

export default withI18n()(CredentialStep);
