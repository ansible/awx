import React from 'react';
import { Link, withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import styled from 'styled-components';
import { Host } from '@types';
import { formatDateString } from '@util/dates';
import { Button, CardBody } from '@patternfly/react-core';
import { DetailList, Detail } from '@components/DetailList';
import CodeMirrorInput from '@components/CodeMirrorInput';

const ActionButtonWrapper = styled.div`
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
  & > :not(:first-child) {
    margin-left: 20px;
  }
`;

function HostDetail({ host, i18n }) {
  const { created, description, id, modified, name, summary_fields } = host;

  let createdBy = '';
  if (created) {
    if (summary_fields.created_by && summary_fields.created_by.username) {
      createdBy = i18n._(
        t`${formatDateString(created)} by ${summary_fields.created_by.username}`
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

  return (
    <CardBody css="padding-top: 20px">
      <DetailList gutter="sm">
        <Detail label={i18n._(t`Name`)} value={name} />
        <Detail label={i18n._(t`Description`)} value={description} />
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
        {/* TODO: Link to user in users */}
        <Detail label={i18n._(t`Created`)} value={createdBy} />
        {/* TODO: Link to user in users */}
        <Detail label={i18n._(t`Last Modified`)} value={modifiedBy} />
        <Detail
          fullWidth
          label={i18n._(t`Variables`)}
          value={
            <CodeMirrorInput
              mode="yaml"
              readOnly
              value={host.variables}
              onChange={() => {}}
              rows={6}
              hasErrors={false}
            />
          }
        />
      </DetailList>
      <ActionButtonWrapper>
        {summary_fields.user_capabilities &&
          summary_fields.user_capabilities.edit && (
            <Button
              aria-label={i18n._(t`edit`)}
              component={Link}
              to={`/hosts/${id}/edit`}
            >
              {i18n._(t`Edit`)}
            </Button>
          )}
      </ActionButtonWrapper>
    </CardBody>
  );
}

HostDetail.propTypes = {
  host: Host.isRequired,
};

export default withI18n()(withRouter(HostDetail));
