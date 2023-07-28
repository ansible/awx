import React from 'react';
import { t } from '@lingui/macro';
import {
  Alert,
  AlertActionLink,
  ClipboardCopyButton,
  CodeBlock,
  CodeBlockAction,
  CodeBlockCode,
  ClipboardCopy,
  Form,
  FormFieldGroupExpandable,
  FormFieldGroupHeader,
  FormGroup,
  Panel,
  CardBody,
} from '@patternfly/react-core';
import {
  TableComposable,
  Thead,
  Tr,
  Th,
  Tbody,
  Td,
} from '@patternfly/react-table';
import { ExternalLinkAltIcon } from '@patternfly/react-icons';
import getDocsBaseUrl from 'util/getDocsBaseUrl';
import { useConfig } from 'contexts/Config';

function ConstructedInventoryHint() {
  const config = useConfig();

  return (
    <Alert
      isExpandable
      isInline
      variant="info"
      title={t`How to use constructed inventory plugin`}
      actionLinks={
        <AlertActionLink
          href={`${getDocsBaseUrl(
            config
          )}/html/userguide/inventories.html#constructed-inventories`}
          component="a"
          target="_blank"
          rel="noopener noreferrer"
        >
          {t`View constructed inventory documentation here`}{' '}
          <ExternalLinkAltIcon />
        </AlertActionLink>
      }
    >
      <span>
        {t`This table gives a few useful parameters of the constructed
               inventory plugin. For the full list of parameters `}{' '}
        <a
          href={t`https://docs.ansible.com/ansible/latest/collections/ansible/builtin/constructed_inventory.html`}
        >{t`view the constructed inventory plugin docs here.`}</a>
      </span>
      <br />
      <br />
      <TableComposable
        aria-label={t`Constructed inventory parameters table`}
        variant="compact"
      >
        <Thead>
          <Tr>
            <Th>{t`Parameter`}</Th>
            <Th>{t`Description`}</Th>
          </Tr>
        </Thead>
        <Tbody>
          <Tr ouiaId="plugin-row">
            <Td dataLabel={t`name`}>
              <code>plugin</code>
              <p style={{ color: 'blue' }}>{t`string`}</p>
              <p style={{ color: 'red' }}>{t`required`}</p>
            </Td>
            <Td dataLabel={t`description`}>
              {t`Token that ensures this is a source file
              for the ‘constructed’ plugin.`}
            </Td>
          </Tr>
          <Tr key="strict">
            <Td dataLabel={t`name`}>
              <code>strict</code>
              <p style={{ color: 'blue' }}>{t`boolean`}</p>
            </Td>
            <Td dataLabel={t`description`}>
              {t`If yes make invalid entries a fatal error, otherwise skip and
              continue.`}{' '}
              <br />
              {t`If users need feedback about the correctness
              of their constructed groups, it is highly recommended
              to use strict: true in the plugin configuration.`}
            </Td>
          </Tr>
          <Tr key="groups">
            <Td dataLabel={t`name`}>
              <code>groups</code>
              <p style={{ color: 'blue' }}>{t`dictionary`}</p>
            </Td>
            <Td dataLabel={t`description`}>
              {t`Add hosts to group based on Jinja2 conditionals.`}
            </Td>
          </Tr>
          <Tr key="compose">
            <Td dataLabel={t`name`}>
              <code>compose</code>
              <p style={{ color: 'blue' }}>{t`dictionary`}</p>
            </Td>
            <Td dataLabel={t`description`}>
              {t`Create vars from jinja2 expressions. This can be useful
              if the constructed groups you define do not contain the expected
              hosts. This can be used to add hostvars from expressions so
              that you know what the resultant values of those expressions are.`}
            </Td>
          </Tr>
        </Tbody>
      </TableComposable>
      <br />
      <br />
      <Panel>
        <CardBody>
          <Form autoComplete="off">
            <b>{t`Constructed inventory examples`}</b>
            <LimitToIntersectionExample />
            <FilterOnNestedGroupExample />
            <HostsByProcessorTypeExample />
          </Form>
        </CardBody>
      </Panel>
    </Alert>
  );
}

function LimitToIntersectionExample() {
  const [copied, setCopied] = React.useState(false);
  const clipboardCopyFunc = (event, text) => {
    navigator.clipboard.writeText(text.toString());
  };

  const onClick = (event, text) => {
    clipboardCopyFunc(event, text);
    setCopied(true);
  };

  const limitToIntersectionLimit = `is_shutdown:&product_dev`;
  const limitToIntersectionCode = `plugin: constructed
strict: true
groups:
  shutdown_in_product_dev: state | default("running") == "shutdown" and account_alias == "product_dev"`;

  return (
    <FormFieldGroupExpandable
      header={
        <FormFieldGroupHeader
          titleText={{
            text: t`Construct 2 groups, limit to intersection`,
            id: 'intersection-example',
          }}
          titleDescription={t`This constructed inventory input 
            creates a group for both of the categories and uses 
            the limit (host pattern) to only return hosts that 
            are in the intersection of those two groups.`}
        />
      }
    >
      <FormGroup label={t`Limit`} fieldId="intersection-example-limit">
        <ClipboardCopy isReadOnly hoverTip={t`Copy`} clickTip={t`Copied`}>
          {limitToIntersectionLimit}
        </ClipboardCopy>
      </FormGroup>
      <FormGroup
        label={t`Source vars`}
        fieldId="intersection-example-source-vars"
      >
        <CodeBlock
          actions={
            <CodeBlockAction>
              <ClipboardCopyButton
                id="intersection-example-source-vars"
                textId="intersection-example-source-vars"
                aria-label={t`Copy to clipboard`}
                onClick={(e) => onClick(e, limitToIntersectionCode)}
                exitDelay={copied ? 1500 : 600}
                maxWidth="110px"
                variant="plain"
                onTooltipHidden={() => setCopied(false)}
              >
                {copied
                  ? t`Successfully copied to clipboard!`
                  : t`Copy to clipboard`}
              </ClipboardCopyButton>
            </CodeBlockAction>
          }
        >
          <CodeBlockCode id="intersection-example-source-vars">
            {limitToIntersectionCode}
          </CodeBlockCode>
        </CodeBlock>
      </FormGroup>
    </FormFieldGroupExpandable>
  );
}
function FilterOnNestedGroupExample() {
  const [copied, setCopied] = React.useState(false);
  const clipboardCopyFunc = (event, text) => {
    navigator.clipboard.writeText(text.toString());
  };

  const onClick = (event, text) => {
    clipboardCopyFunc(event, text);
    setCopied(true);
  };

  const nestedGroupsInventoryLimit = `groupA`;
  const nestedGroupsInventorySourceVars = `plugin: constructed`;
  const nestedGroupsInventory = `all:
  children:
    groupA:
      children:
        groupB:
          hosts:
            host1: {}
      vars:
        filter_var: filter_val
    ungrouped:
      hosts:
        host2: {}`;

  return (
    <FormFieldGroupExpandable
      header={
        <FormFieldGroupHeader
          titleText={{
            text: t`Filter on nested group name`,
            id: 'nested-groups-example',
          }}
          titleDescription={t`This constructed inventory input
            creates a group for both of the categories and uses
            the limit (host pattern) to only return hosts that
            are in the intersection of those two groups.`}
        />
      }
    >
      <FormGroup>
        <p>{t`Nested groups inventory definition:`}</p>
        <CodeBlock>
          <CodeBlockCode id="nested-groups-example-inventory">
            {nestedGroupsInventory}
          </CodeBlockCode>
        </CodeBlock>
      </FormGroup>
      <FormGroup label={t`Limit`} fieldId="nested-groups-example-limit">
        <ClipboardCopy isReadOnly hoverTip={t`Copy`} clickTip={t`Copied`}>
          {nestedGroupsInventoryLimit}
        </ClipboardCopy>
      </FormGroup>
      <FormGroup
        label={t`Source vars`}
        fieldId="nested-groups-example-source-vars"
      >
        <CodeBlock
          actions={
            <CodeBlockAction>
              <ClipboardCopyButton
                id="nested-groups-example-source-vars"
                textId="nested-groups-example-source-vars"
                aria-label={t`Copy to clipboard`}
                onClick={(e) => onClick(e, nestedGroupsInventorySourceVars)}
                exitDelay={copied ? 1500 : 600}
                maxWidth="110px"
                variant="plain"
                onTooltipHidden={() => setCopied(false)}
              >
                {copied
                  ? t`Successfully copied to clipboard!`
                  : t`Copy to clipboard`}
              </ClipboardCopyButton>
            </CodeBlockAction>
          }
        >
          <CodeBlockCode id="nested-groups-example-source-vars">
            {nestedGroupsInventorySourceVars}
          </CodeBlockCode>
        </CodeBlock>
      </FormGroup>
    </FormFieldGroupExpandable>
  );
}
function HostsByProcessorTypeExample() {
  const [copied, setCopied] = React.useState(false);
  const clipboardCopyFunc = (event, text) => {
    navigator.clipboard.writeText(text.toString());
  };

  const onClick = (event, text) => {
    clipboardCopyFunc(event, text);
    setCopied(true);
  };

  const hostsByProcessorLimit = `intel_hosts`;
  const hostsByProcessorSourceVars = `plugin: constructed
  strict: true
  groups:
    intel_hosts: "GenuineIntel" in ansible_processor`;

  return (
    <FormFieldGroupExpandable
      header={
        <FormFieldGroupHeader
          titleText={{
            text: t`Hosts by processor type`,
            id: 'processor-example',
          }}
          titleDescription="It is hard to give a specification for
            the inventory for Ansible facts, because to populate
            the system facts you need to run a playbook against
            the inventory that has `gather_facts: true`. The
            actual facts will differ system-to-system."
        />
      }
    >
      <FormGroup label={t`Limit`} fieldId="processor-example-limit">
        <ClipboardCopy isReadOnly hoverTip={t`Copy`} clickTip={t`Copied`}>
          {hostsByProcessorLimit}
        </ClipboardCopy>
      </FormGroup>
      <FormGroup label={t`Source vars`} fieldId="processor-example-source-vars">
        <CodeBlock
          actions={
            <CodeBlockAction>
              <ClipboardCopyButton
                id="processor-example-source-vars"
                textId="processor-example-source-vars"
                aria-label={t`Copy to clipboard`}
                onClick={(e) => onClick(e, hostsByProcessorSourceVars)}
                exitDelay={copied ? 1500 : 600}
                maxWidth="110px"
                variant="plain"
                onTooltipHidden={() => setCopied(false)}
              >
                {copied
                  ? t`Successfully copied to clipboard!`
                  : t`Copy to clipboard`}
              </ClipboardCopyButton>
            </CodeBlockAction>
          }
        >
          <CodeBlockCode id="processor-example-source-vars">
            {hostsByProcessorSourceVars}
          </CodeBlockCode>
        </CodeBlock>
      </FormGroup>
    </FormFieldGroupExpandable>
  );
}

export default ConstructedInventoryHint;
