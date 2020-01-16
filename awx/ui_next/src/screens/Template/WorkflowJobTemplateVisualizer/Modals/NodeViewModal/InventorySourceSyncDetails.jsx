import React, { useEffect, useState } from 'react';
import { withI18n } from '@lingui/react';
import { Trans } from '@lingui/macro';
import { t } from '@lingui/macro';
import { InventorySourcesAPI } from '@api';
import ContentError from '@components/ContentError';
import ContentLoading from '@components/ContentLoading';
import { DetailList, Detail } from '@components/DetailList';
import { VariablesDetail } from '@components/CodeMirrorInput';
import { CredentialChip } from '@components/Chip';

function InventorySourceSyncDetails({ i18n, node }) {
  const [inventorySource, setInventorySource] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [noReadAccess, setNoReadAccess] = useState(false);
  const [contentError, setContentError] = useState(null);
  const [optionsActions, setOptionsActions] = useState(null);

  useEffect(() => {
    async function fetchInventorySource() {
      try {
        const [
          { data },
          {
            data: { actions },
          },
        ] = await Promise.all([
          InventorySourcesAPI.readDetail(node.unifiedJobTemplate.id),
          InventorySourcesAPI.readOptions(),
        ]);
        setInventorySource(data);
        setOptionsActions(actions);
      } catch (err) {
        if (err.response.status === 403) {
          setNoReadAccess(true);
        } else {
          setContentError(err);
        }
      } finally {
        setIsLoading(false);
      }
    }
    fetchInventorySource();
  }, []);

  if (isLoading) {
    return <ContentLoading />;
  }

  if (contentError) {
    return <ContentError error={contentError} />;
  }

  if (noReadAccess) {
    return (
      <>
        <p>
          <Trans>
            Your account does not have read access to this inventory source so
            the displayed details will be limited.
          </Trans>
        </p>
        <br />
        <DetailList gutter="sm">
          <Detail
            label={i18n._(t`Node Type`)}
            value={i18n._(t`Inventory Source Sync`)}
          />
          <Detail
            label={i18n._(t`Name`)}
            value={node.unifiedJobTemplate.name}
          />
          <Detail
            label={i18n._(t`Description`)}
            value={node.unifiedJobTemplate.description}
          />
        </DetailList>
      </>
    );
  }

  const {
    custom_virtualenv,
    description,
    group_by,
    instance_filters,
    name,
    source,
    source_path,
    source_regions,
    source_script,
    source_vars,
    summary_fields,
    timeout,
    verbosity,
  } = inventorySource;

  let sourceValue = '';
  let verbosityValue = '';

  optionsActions.GET.source.choices.forEach(choice => {
    if (choice[0] === source) {
      sourceValue = choice[1];
    }
  });

  optionsActions.GET.verbosity.choices.forEach(choice => {
    if (choice[0] === verbosity) {
      verbosityValue = choice[1];
    }
  });

  return (
    <DetailList gutter="sm">
      <Detail
        label={i18n._(t`Node Type`)}
        value={i18n._(t`Inventory Source Sync`)}
      />
      <Detail label={i18n._(t`Name`)} value={name} />
      <Detail label={i18n._(t`Description`)} value={description} />
      {summary_fields.inventory && (
        <Detail
          label={i18n._(t`Inventory`)}
          value={summary_fields.inventory.name}
        />
      )}
      {summary_fields.credential && (
        <Detail
          label={i18n._(t`Credential`)}
          value={
            <CredentialChip
              key={summary_fields.credential.id}
              credential={summary_fields.credential}
              isReadOnly
            />
          }
        />
      )}
      <Detail label={i18n._(t`Source`)} value={sourceValue} />
      <Detail label={i18n._(t`Source Path`)} value={source_path} />
      <Detail label={i18n._(t`Source Script`)} value={source_script} />
      {/* this should probably be tags built from OPTIONS*/}
      <Detail label={i18n._(t`Source Regions`)} value={source_regions} />
      <Detail label={i18n._(t`Instance Filters`)} value={instance_filters} />
      {/* this should probably be tags built from OPTIONS */}
      <Detail label={i18n._(t`Only Group By`)} value={group_by} />
      <Detail
        label={i18n._(t`Timeout`)}
        value={`${timeout} ${i18n._(t`Seconds`)}`}
      />
      <Detail
        label={i18n._(t`Ansible Environment`)}
        value={custom_virtualenv}
      />
      <Detail label={i18n._(t`Verbosity`)} value={verbosityValue} />
      <VariablesDetail
        label={i18n._(t`Variables`)}
        value={source_vars}
        rows={4}
      />
    </DetailList>
  );
}

export default withI18n()(InventorySourceSyncDetails);
