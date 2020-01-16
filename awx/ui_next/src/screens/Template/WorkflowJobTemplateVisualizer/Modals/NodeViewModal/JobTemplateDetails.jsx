import React, { useEffect, useState } from 'react';
import { withI18n } from '@lingui/react';
import { Trans } from '@lingui/macro';
import { t } from '@lingui/macro';
import jsyaml from 'js-yaml';
import styled from 'styled-components';
import { JobTemplatesAPI, WorkflowJobTemplateNodesAPI } from '@api';
import ContentError from '@components/ContentError';
import ContentLoading from '@components/ContentLoading';
import { DetailList, Detail } from '@components/DetailList';
import { ChipGroup, Chip, CredentialChip } from '@components/Chip';
import { VariablesDetail } from '@components/CodeMirrorInput';

const Overridden = styled.div`
  color: var(--pf-global--warning-color--100);
`;

function JobTemplateDetails({ i18n, node }) {
  const [jobTemplate, setJobTemplate] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [noReadAccess, setNoReadAccess] = useState(false);
  const [contentError, setContentError] = useState(null);
  const [optionsActions, setOptionsActions] = useState(null);
  const [instanceGroups, setInstanceGroups] = useState([]);
  const [nodeCredentials, setNodeCredentials] = useState([]);
  const [launchConf, setLaunchConf] = useState(null);

  useEffect(() => {
    async function fetchJobTemplate() {
      try {
        const [
          { data },
          {
            data: { results: instanceGroups },
          },
          { data: launchConf },
          {
            data: { actions },
          },
          {
            data: { results: nodeCredentials },
          },
        ] = await Promise.all([
          JobTemplatesAPI.readDetail(node.unifiedJobTemplate.id),
          JobTemplatesAPI.readInstanceGroups(node.unifiedJobTemplate.id),
          JobTemplatesAPI.readLaunch(node.unifiedJobTemplate.id),
          JobTemplatesAPI.readOptions(),
          WorkflowJobTemplateNodesAPI.readCredentials(
            node.originalNodeObject.id
          ),
        ]);
        setJobTemplate(data);
        setInstanceGroups(instanceGroups);
        setLaunchConf(launchConf);
        setOptionsActions(actions);
        setNodeCredentials(nodeCredentials);
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
    fetchJobTemplate();
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
            Your account does not have read access to this job template so the
            displayed details will be limited.
          </Trans>
        </p>
        <br />
        <DetailList gutter="sm">
          <Detail
            label={i18n._(t`Node Type`)}
            value={i18n._(t`Job Template`)}
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
    job_type: nodeJobType,
    limit: nodeLimit,
    scm_branch: nodeScmBranch,
    inventory: nodeInventory,
    verbosity: nodeVerbosity,
    job_tags: nodeJobTags,
    skip_tags: nodeSkipTags,
    diff_mode: nodeDiffMode,
    extra_data: nodeExtraData,
    summary_fields: nodeSummaryFields,
  } = node.originalNodeObject;

  let {
    ask_job_type_on_launch,
    ask_limit_on_launch,
    ask_scm_branch_on_launch,
    ask_inventory_on_launch,
    ask_verbosity_on_launch,
    ask_tags_on_launch,
    ask_skip_tags_on_launch,
    ask_diff_mode_on_launch,
    ask_credential_on_launch,
    ask_variables_on_launch,
    description,
    diff_mode,
    extra_vars,
    forks,
    host_config_key,
    job_slice_count,
    job_tags,
    job_type,
    name,
    limit,
    playbook,
    skip_tags,
    timeout,
    summary_fields,
    verbosity,
    scm_branch,
    inventory,
  } = jobTemplate;

  const jobTypeOverridden =
    ask_job_type_on_launch && nodeJobType !== null && job_type !== nodeJobType;
  const limitOverridden =
    ask_limit_on_launch && nodeLimit !== null && limit !== nodeLimit;
  const scmBranchOverridden =
    ask_scm_branch_on_launch &&
    nodeScmBranch !== null &&
    scm_branch !== nodeScmBranch;
  const inventoryOverridden =
    ask_inventory_on_launch &&
    nodeInventory !== null &&
    inventory !== nodeInventory;
  const verbosityOverridden =
    ask_verbosity_on_launch &&
    nodeVerbosity !== null &&
    verbosity !== nodeVerbosity;
  const jobTagsOverridden =
    ask_tags_on_launch && nodeJobTags !== null && job_tags !== nodeJobTags;
  const skipTagsOverridden =
    ask_skip_tags_on_launch &&
    nodeSkipTags !== null &&
    skip_tags !== nodeSkipTags;
  const diffModeOverridden =
    ask_diff_mode_on_launch &&
    nodeDiffMode !== null &&
    diff_mode !== nodeDiffMode;
  const credentialOverridden =
    ask_credential_on_launch && nodeCredentials.length > 0;
  let variablesOverridden = false;
  let variablesToShow = extra_vars;

  const deepObjectMatch = (obj1, obj2) => {
    if (obj1 === obj2) {
      return true;
    }

    if (
      obj1 === null ||
      obj2 === null ||
      typeof obj1 !== 'object' ||
      typeof obj2 !== 'object'
    ) {
      return false;
    }

    const obj1Keys = Object.keys(obj1);
    const obj2Keys = Object.keys(obj2);

    if (obj1Keys.length !== obj2Keys.length) {
      return false;
    }

    for (let key of obj1Keys) {
      if (!obj2Keys.includes(key) || !deepObjectMatch(obj1[key], obj2[key])) {
        return false;
      }
    }

    return true;
  };

  if (ask_variables_on_launch || launchConf.survey_enabled) {
    // we need to check to see if the extra vars are different from the defaults
    // but we'll need to do some normalization.  Convert both to JSON objects
    // and then compare.

    let jsonifiedExtraVars = {};
    let jsonifiedExtraData = {};

    // extra_vars has to be a string
    if (typeof extra_vars === 'string') {
      if (
        extra_vars === '{}' ||
        extra_vars === 'null' ||
        extra_vars === '' ||
        extra_vars === '""'
      ) {
        jsonifiedExtraVars = {};
      } else {
        try {
          // try to turn the string into json
          jsonifiedExtraVars = JSON.parse(extra_vars);
        } catch (jsonParseError) {
          try {
            // do safeLoad, which well error if not valid yaml
            jsonifiedExtraVars = jsyaml.safeLoad(extra_vars);
          } catch (yamlLoadError) {
            setContentError(yamlLoadError);
          }
        }
      }
    } else {
      setContentError(
        Error(i18n._(t`Error parsing extra variables from the job template`))
      );
    }

    // extra_data on a node can be either a string or an object...
    if (typeof nodeExtraData === 'string') {
      if (
        nodeExtraData === '{}' ||
        nodeExtraData === 'null' ||
        nodeExtraData === '' ||
        nodeExtraData === '""'
      ) {
        jsonifiedExtraData = {};
      } else {
        try {
          // try to turn the string into json
          jsonifiedExtraData = JSON.parse(nodeExtraData);
        } catch (error) {
          try {
            // do safeLoad, which well error if not valid yaml
            jsonifiedExtraData = jsyaml.safeLoad(nodeExtraData);
          } catch (yamlLoadError) {
            setContentError(yamlLoadError);
          }
        }
      }
    } else if (typeof nodeExtraData === 'object') {
      jsonifiedExtraData = nodeExtraData;
    } else {
      setContentError(
        Error(i18n._(t`Error parsing extra variables from the node`))
      );
    }

    if (!deepObjectMatch(jsonifiedExtraVars, jsonifiedExtraData)) {
      variablesOverridden = true;
      variablesToShow = jsyaml.safeDump(
        Object.assign(jsonifiedExtraVars, jsonifiedExtraData)
      );
    }
  }

  let credentialsToShow = summary_fields.credentials;

  if (credentialOverridden) {
    credentialsToShow = [...nodeCredentials];

    // adds vault_id to the credentials we get back from
    // fetching the JT
    launchConf.defaults.credentials.forEach(launchCred => {
      if (launchCred.vault_id) {
        summary_fields.credentials[
          summary_fields.credentials.findIndex(
            defaultCred => defaultCred.id === launchCred.id
          )
        ].vault_id = launchCred.vault_id;
      }
    });

    summary_fields.credentials.forEach(defaultCred => {
      if (
        !nodeCredentials.some(
          overrideCredential =>
            (defaultCred.kind === overrideCredential.kind &&
              (!defaultCred.vault_id && !overrideCredential.inputs.vault_id)) ||
            (defaultCred.vault_id &&
              overrideCredential.inputs.vault_id &&
              defaultCred.vault_id === overrideCredential.inputs.vault_id)
        )
      ) {
        credentialsToShow.push(defaultCred);
      }
    });
  }

  let verbosityToShow = '';

  optionsActions.GET.verbosity.choices.forEach(choice => {
    if (
      verbosityOverridden
        ? choice[0] === nodeVerbosity
        : choice[0] === verbosity
    ) {
      verbosityToShow = choice[1];
    }
  });

  const jobTagsToShow = jobTagsOverridden ? nodeJobTags : job_tags;
  const skipTagsToShow = skipTagsOverridden ? nodeSkipTags : skip_tags;

  return (
    <>
      <DetailList gutter="sm">
        <Detail label={i18n._(t`Node Type`)} value={i18n._(t`Job Template`)} />
        <Detail label={i18n._(t`Name`)} value={name} />
        <Detail label={i18n._(t`Description`)} value={description} />
        <Detail
          label={
            jobTypeOverridden ? (
              <Overridden>* {i18n._(t`Job Type`)}</Overridden>
            ) : (
              i18n._(t`Job Type`)
            )
          }
          value={jobTypeOverridden ? nodeJobType : job_type}
        />
        <Detail
          label={
            inventoryOverridden ? (
              <Overridden>* {i18n._(t`Inventory`)}</Overridden>
            ) : (
              i18n._(t`Inventory`)
            )
          }
          value={
            inventoryOverridden
              ? nodeSummaryFields.inventory.name
              : summary_fields.inventory.name
          }
          alwaysVisible={inventoryOverridden}
        />
        {summary_fields.project && (
          <Detail
            label={i18n._(t`Project`)}
            value={summary_fields.project.name}
          />
        )}
        <Detail
          label={
            scmBranchOverridden ? (
              <Overridden>* {i18n._(t`SCM Branch`)}</Overridden>
            ) : (
              i18n._(t`SCM Branch`)
            )
          }
          value={scmBranchOverridden ? nodeScmBranch : scm_branch}
          alwaysVisible={scmBranchOverridden}
        />
        <Detail label={i18n._(t`Playbook`)} value={playbook} />
        <Detail label={i18n._(t`Forks`)} value={forks || '0'} />
        <Detail
          label={
            limitOverridden ? (
              <Overridden>* {i18n._(t`Limit`)}</Overridden>
            ) : (
              i18n._(t`Limit`)
            )
          }
          value={limitOverridden ? nodeLimit : limit}
          alwaysVisible={limitOverridden}
        />
        <Detail
          label={
            verbosityOverridden ? (
              <Overridden>* {i18n._(t`Verbosity`)}</Overridden>
            ) : (
              i18n._(t`Verbosity`)
            )
          }
          value={verbosityToShow}
        />
        <Detail label={i18n._(t`Timeout`)} value={timeout || '0'} />
        <Detail
          label={
            diffModeOverridden ? (
              <Overridden>* {i18n._(t`Show Changes`)}</Overridden>
            ) : (
              i18n._(t`Show Changes`)
            )
          }
          value={
            (diffModeOverridden
            ? nodeDiffMode
            : diff_mode)
              ? i18n._(t`On`)
              : i18n._(t`Off`)
          }
        />
        <Detail label={i18n._(t` Job Slicing`)} value={job_slice_count} />
        {host_config_key && (
          <>
            <Detail
              label={i18n._(t`Host Config Key`)}
              value={host_config_key}
            />
            <Detail
              label={i18n._(t`Provisioning Callback URL`)}
              value={generateCallBackUrl}
            />
          </>
        )}
        <Detail
          fullWidth
          label={
            credentialOverridden ? (
              <Overridden>* {i18n._(t`Credentials`)}</Overridden>
            ) : (
              i18n._(t`Credentials`)
            )
          }
          value={
            credentialsToShow.length > 0 && (
              <ChipGroup numChips={5}>
                {credentialsToShow.map(c => (
                  <CredentialChip key={c.id} credential={c} isReadOnly />
                ))}
              </ChipGroup>
            )
          }
          alwaysVisible={credentialOverridden}
        />
        {summary_fields.labels && summary_fields.labels.results.length > 0 && (
          <Detail
            fullWidth
            label={i18n._(t`Labels`)}
            value={
              <ChipGroup numChips={5}>
                {summary_fields.labels.results.map(l => (
                  <Chip key={l.id} isReadOnly>
                    {l.name}
                  </Chip>
                ))}
              </ChipGroup>
            }
          />
        )}
        {instanceGroups.length > 0 && (
          <Detail
            fullWidth
            label={i18n._(t`Instance Groups`)}
            value={
              <ChipGroup numChips={5}>
                {instanceGroups.map(ig => (
                  <Chip key={ig.id} isReadOnly>
                    {ig.name}
                  </Chip>
                ))}
              </ChipGroup>
            }
          />
        )}
        <Detail
          fullWidth
          label={
            jobTagsOverridden ? (
              <Overridden>* {i18n._(t`Job Tags`)}</Overridden>
            ) : (
              i18n._(t`Job Tags`)
            )
          }
          value={
            jobTagsOverridden.length > 0 && (
              <ChipGroup numChips={5}>
                {jobTagsToShow.split(',').map(jobTag => (
                  <Chip key={jobTag} isReadOnly>
                    {jobTag}
                  </Chip>
                ))}
              </ChipGroup>
            )
          }
          alwaysVisible={jobTagsOverridden}
        />
        <Detail
          fullWidth
          label={
            skipTagsOverridden ? (
              <Overridden>* {i18n._(t`Skip Tags`)}</Overridden>
            ) : (
              i18n._(t`Skip Tags`)
            )
          }
          value={
            skipTagsToShow.length > 0 && (
              <ChipGroup numChips={5}>
                {skipTagsToShow.split(',').map(skipTag => (
                  <Chip key={skipTag} isReadOnly>
                    {skipTag}
                  </Chip>
                ))}
              </ChipGroup>
            )
          }
          alwaysVisible={skipTagsOverridden}
        />
        <VariablesDetail
          label={
            variablesOverridden ? (
              <Overridden>* {i18n._(t`Variables`)}</Overridden>
            ) : (
              i18n._(t`Variables`)
            )
          }
          value={variablesToShow}
          rows={4}
        />
      </DetailList>
      {(jobTypeOverridden ||
        limitOverridden ||
        scmBranchOverridden ||
        inventoryOverridden ||
        verbosityOverridden ||
        jobTagsOverridden ||
        skipTagsOverridden ||
        diffModeOverridden ||
        credentialOverridden ||
        variablesOverridden) && (
        <>
          <br />
          <Overridden>
            <b>
              <Trans>
                * Values for these fields differ from the job template's default
              </Trans>
            </b>
          </Overridden>
        </>
      )}
    </>
  );
}

export default withI18n()(JobTemplateDetails);
