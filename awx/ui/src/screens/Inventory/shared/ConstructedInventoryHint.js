import React from 'react';
import { t } from '@lingui/macro';
import {
  Alert,
  AlertActionLink,
  CodeBlock,
  CodeBlockAction,
  CodeBlockCode,
  ClipboardCopyButton,
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
  const [copied, setCopied] = React.useState(false);

  const clipboardCopyFunc = (event, text) => {
    navigator.clipboard.writeText(text.toString());
  };

  const onClick = (event, text) => {
    clipboardCopyFunc(event, text);
    setCopied(true);
  };

  const pluginSample = `plugin: constructed
strict: true
use_vars_plugins: true
groups:
  shutdown: resolved_state == "shutdown"
  shutdown_in_product_dev: resolved_state == "shutdown" and account_alias == "product_dev"
compose:
  resolved_state: state | default("running")`;

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
        >
          {t`View constructed plugin documentation here`}{' '}
          <ExternalLinkAltIcon />
        </AlertActionLink>
      }
    >
      <span>{t`WIP - More to come...`}</span>
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
          <Tr key="use_vars_plugins">
            <Td dataLabel={t`name`}>
              <code>use_vars_plugins</code>
              <p style={{ color: 'blue' }}>{t`string`}</p>
            </Td>
            <Td dataLabel={t`description`}>
              {t`Normally, for performance reasons, vars plugins get 
              executed after the inventory sources complete the 
              base inventory, this option allows for getting vars 
              related to hosts/groups from those plugins.`}
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
              {t`Create vars from jinja2 expressions.`}
            </Td>
          </Tr>
        </Tbody>
      </TableComposable>
      <br />
      <br />
      <b>{t`Sample constructed inventory plugin:`}</b>
      <CodeBlock
        actions={
          <CodeBlockAction>
            <ClipboardCopyButton
              id="basic-copy-button"
              textId="code-content"
              aria-label={t`Copy to clipboard`}
              onClick={(e) => onClick(e, pluginSample)}
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
        <CodeBlockCode id="code-content">{pluginSample}</CodeBlockCode>
      </CodeBlock>
    </Alert>
  );
}

export default ConstructedInventoryHint;
