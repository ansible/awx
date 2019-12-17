import React from 'react';
import { Link, withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import styled from 'styled-components';
import { Host } from '@types';
import { Button, CardBody } from '@patternfly/react-core';
import { DetailList, Detail, UserDateDetail } from '@components/DetailList';
import { VariablesDetail } from '@components/CodeMirrorInput';

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

  return (
    <CardBody>
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
        <UserDateDetail
          label={i18n._(t`Created`)}
          date={created}
          user={summary_fields.created_by}
        />
        <UserDateDetail
          label={i18n._(t`Last Modified`)}
          date={modified}
          user={summary_fields.modified_by}
        />
        <VariablesDetail
          label={i18n._(t`Variables`)}
          value={host.variables}
          rows={6}
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
