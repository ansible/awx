import React, { Component } from 'react';
import { Link, withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import {
  CardBody,
  Button,
  TextList,
  TextListItem,
  TextListItemVariants,
  TextListVariants,
} from '@patternfly/react-core';
import styled from 'styled-components';
import { t } from '@lingui/macro';

import ContentError from '@components/ContentError';
import LaunchButton from '@components/LaunchButton';
import ContentLoading from '@components/ContentLoading';
import { ChipGroup, Chip, CredentialChip } from '@components/Chip';
import { DetailList, Detail } from '@components/DetailList';
import { formatDateString } from '@util/dates';
import { JobTemplatesAPI } from '@api';

const ButtonGroup = styled.div`
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
  & > :not(:first-child) {
    margin-left: 20px;
  }
`;
class JobTemplateDetail extends Component {
  constructor(props) {
    super(props);
    this.state = {
      contentError: null,
      hasContentLoading: true,
      instanceGroups: [],
    };
    this.readInstanceGroups = this.readInstanceGroups.bind(this);
  }

  componentDidMount() {
    this.readInstanceGroups();
  }

  async readInstanceGroups() {
    const { match } = this.props;
    try {
      const { data } = await JobTemplatesAPI.readInstanceGroups(
        match.params.id
      );
      this.setState({ instanceGroups: [...data.results] });
    } catch (err) {
      this.setState({ contentError: err });
    } finally {
      this.setState({ hasContentLoading: false });
    }
  }

  render() {
    const {
      template: {
        allow_simultaneous,
        become_enabled,
        created,
        description,
        diff_mode,
        forks,
        host_config_key,
        job_slice_count,
        job_tags,
        job_type,
        name,
        limit,
        modified,
        playbook,
        skip_tags,
        timeout,
        summary_fields,
        use_fact_cache,
        url,
        verbosity,
      },
      hasTemplateLoading,
      template,
      i18n,
      match,
    } = this.props;
    const canLaunch = summary_fields.user_capabilities.start;
    const { instanceGroups, hasContentLoading, contentError } = this.state;
    const verbosityOptions = [
      { verbosity: 0, details: i18n._(t`0 (Normal)`) },
      { verbosity: 1, details: i18n._(t`1 (Verbose)`) },
      { verbosity: 2, details: i18n._(t`2 (More Verbose)`) },
      { verbosity: 3, details: i18n._(t`3 (Debug)`) },
      { verbosity: 4, details: i18n._(t`4 (Connection Debug)`) },
      { verbosity: 5, details: i18n._(t`5 (WinRM Debug)`) },
    ];
    const verbosityDetails = verbosityOptions.filter(
      option => option.verbosity === verbosity
    );
    const generateCallBackUrl = `${window.location.origin + url}callback/`;
    const isInitialized = !hasTemplateLoading && !hasContentLoading;

    const renderOptionsField =
      become_enabled || host_config_key || allow_simultaneous || use_fact_cache;

    let createdBy = '';
    if (created) {
      if (summary_fields.created_by && summary_fields.created_by.username) {
        createdBy = i18n._(
          t`${formatDateString(created)} by ${
            summary_fields.created_by.username
          }`
        );
      } else {
        createdBy = formatDateString(created);
      }
    }

    let modifiedBy = '';
    if (modified) {
      if (summary_fields.modified_by && summary_fields.modified_by.username) {
        modifiedBy = i18n._(
          t`${formatDateString(modified)} by ${
            summary_fields.modified_by.username
          }`
        );
      } else {
        modifiedBy = formatDateString(modified);
      }
    }

    const renderOptions = (
      <TextList component={TextListVariants.ul}>
        {become_enabled && (
          <TextListItem component={TextListItemVariants.li}>
            {i18n._(t`Enable Privilege Escalation`)}
          </TextListItem>
        )}
        {host_config_key && (
          <TextListItem component={TextListItemVariants.li}>
            {i18n._(t`Allow Provisioning Callbacks`)}
          </TextListItem>
        )}
        {allow_simultaneous && (
          <TextListItem component={TextListItemVariants.li}>
            {i18n._(t`Enable Concurrent Jobs`)}
          </TextListItem>
        )}
        {use_fact_cache && (
          <TextListItem component={TextListItemVariants.li}>
            {i18n._(t`Use Fact Cache`)}
          </TextListItem>
        )}
      </TextList>
    );

    if (contentError) {
      return <ContentError error={contentError} />;
    }

    if (hasContentLoading) {
      return <ContentLoading />;
    }

    return (
      isInitialized && (
        <CardBody css="padding-top: 20px;">
          <DetailList gutter="sm">
            <Detail label={i18n._(t`Name`)} value={name} />
            <Detail label={i18n._(t`Description`)} value={description} />
            <Detail label={i18n._(t`Job Type`)} value={job_type} />
            {summary_fields.inventory && (
              <Detail
                label={i18n._(t`Inventory`)}
                value={
                  <Link
                    to={`/inventories/${
                      summary_fields.inventory.kind === 'smart'
                        ? 'smart_inventory'
                        : 'inventory'
                    }/${summary_fields.inventory.id}/details`}
                  >
                    {summary_fields.inventory.name}
                  </Link>
                }
              />
            )}
            {summary_fields.project && (
              <Detail
                label={i18n._(t`Project`)}
                value={
                  <Link to={`/projects/${summary_fields.project.id}/details`}>
                    {summary_fields.project.name}
                  </Link>
                }
              />
            )}
            <Detail label={i18n._(t`Playbook`)} value={playbook} />
            <Detail label={i18n._(t`Forks`)} value={forks || '0'} />
            <Detail label={i18n._(t`Limit`)} value={limit} />
            <Detail
              label={i18n._(t`Verbosity`)}
              value={verbosityDetails[0].details}
            />
            <Detail label={i18n._(t`Timeout`)} value={timeout || '0'} />
            {createdBy && (
              <Detail
                label={i18n._(t`Created`)}
                value={createdBy} // TODO: link to user in users
              />
            )}
            {modifiedBy && (
              <Detail
                label={i18n._(t`Last Modified`)}
                value={modifiedBy} // TODO: link to user in users
              />
            )}
            <Detail
              label={i18n._(t`Show Changes`)}
              value={diff_mode ? 'On' : 'Off'}
            />
            <Detail label={i18n._(t` Job Slicing`)} value={job_slice_count} />
            {host_config_key && (
              <React.Fragment>
                <Detail
                  label={i18n._(t`Host Config Key`)}
                  value={host_config_key}
                />
                <Detail
                  label={i18n._(t`Provisioning Callback URL`)}
                  value={generateCallBackUrl}
                />
              </React.Fragment>
            )}
            {renderOptionsField && (
              <Detail label={i18n._(t`Options`)} value={renderOptions} />
            )}
            {summary_fields.credentials &&
              summary_fields.credentials.length > 0 && (
                <Detail
                  fullWidth
                  label={i18n._(t`Credentials`)}
                  value={
                    <ChipGroup showOverflowAfter={5}>
                      {summary_fields.credentials.map(c => (
                        <CredentialChip key={c.id} credential={c} isReadOnly />
                      ))}
                    </ChipGroup>
                  }
                />
              )}
            {summary_fields.labels && summary_fields.labels.results.length > 0 && (
              <Detail
                fullWidth
                label={i18n._(t`Labels`)}
                value={
                  <ChipGroup showOverflowAfter={5}>
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
                  <ChipGroup showOverflowAfter={5}>
                    {instanceGroups.map(ig => (
                      <Chip key={ig.id} isReadOnly>
                        {ig.name}
                      </Chip>
                    ))}
                  </ChipGroup>
                }
              />
            )}
            {job_tags && job_tags.length > 0 && (
              <Detail
                fullWidth
                label={i18n._(t`Job tags`)}
                value={
                  <ChipGroup showOverflowAfter={5}>
                    {job_tags.split(',').map(jobTag => (
                      <Chip key={jobTag} isReadOnly>
                        {jobTag}
                      </Chip>
                    ))}
                  </ChipGroup>
                }
              />
            )}
            {skip_tags && skip_tags.length > 0 && (
              <Detail
                fullWidth
                label={i18n._(t`Skip tags`)}
                value={
                  <ChipGroup showOverflowAfter={5}>
                    {skip_tags.split(',').map(skipTag => (
                      <Chip key={skipTag} isReadOnly>
                        {skipTag}
                      </Chip>
                    ))}
                  </ChipGroup>
                }
              />
            )}
          </DetailList>
          <ButtonGroup>
            {summary_fields.user_capabilities.edit && (
              <Button
                component={Link}
                to={`/templates/${match.params.templateType}/${match.params.id}/edit`}
                aria-label={i18n._(t`Edit`)}
              >
                {i18n._(t`Edit`)}
              </Button>
            )}
            {canLaunch && (
              <LaunchButton resource={template} aria-label={i18n._(t`Launch`)}>
                {({ handleLaunch }) => (
                  <Button
                    variant="secondary"
                    type="submit"
                    onClick={handleLaunch}
                  >
                    {i18n._(t`Launch`)}
                  </Button>
                )}
              </LaunchButton>
            )}
          </ButtonGroup>
        </CardBody>
      )
    );
  }
}
export { JobTemplateDetail as _JobTemplateDetail };
export default withI18n()(withRouter(JobTemplateDetail));
