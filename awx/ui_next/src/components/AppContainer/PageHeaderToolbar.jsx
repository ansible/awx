import React, { useCallback, useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Link } from 'react-router-dom';
import styled from 'styled-components';
import {
  Badge,
  Dropdown,
  DropdownItem,
  DropdownToggle,
  DropdownPosition,
  PageHeaderTools,
  PageHeaderToolsGroup,
  PageHeaderToolsItem,
  Tooltip,
} from '@patternfly/react-core';
import {
  BellIcon,
  QuestionCircleIcon,
  UserIcon,
} from '@patternfly/react-icons';
import { WorkflowApprovalsAPI } from '../../api';
import useRequest from '../../util/useRequest';
import getDocsBaseUrl from '../../util/getDocsBaseUrl';
import { useConfig } from '../../contexts/Config';
import useWsPendingApprovalCount from './useWsPendingApprovalCount';

const PendingWorkflowApprovals = styled.div`
  display: flex;
  align-items: center;
  padding: 10px;
  margin-right: 10px;
`;

const PendingWorkflowApprovalBadge = styled(Badge)`
  margin-left: 10px;
`;

function PageHeaderToolbar({
  isAboutDisabled,
  onAboutClick,
  onLogoutClick,
  loggedInUser,
  i18n,
}) {
  const [isHelpOpen, setIsHelpOpen] = useState(false);
  const [isUserOpen, setIsUserOpen] = useState(false);
  const config = useConfig();

  const {
    request: fetchPendingApprovalCount,
    result: pendingApprovals,
  } = useRequest(
    useCallback(async () => {
      const {
        data: { count },
      } = await WorkflowApprovalsAPI.read({
        status: 'pending',
        page_size: 1,
      });
      return count;
    }, []),
    0
  );

  const pendingApprovalsCount = useWsPendingApprovalCount(
    pendingApprovals,
    fetchPendingApprovalCount
  );

  useEffect(() => {
    fetchPendingApprovalCount();
  }, [fetchPendingApprovalCount]);

  const handleHelpSelect = () => {
    setIsHelpOpen(!isHelpOpen);
  };

  const handleUserSelect = () => {
    setIsUserOpen(!isUserOpen);
  };
  return (
    <PageHeaderTools>
      <PageHeaderToolsGroup>
        <Tooltip
          position="bottom"
          content={i18n._(t`Pending Workflow Approvals`)}
        >
          <PageHeaderToolsItem>
            <Link to="/workflow_approvals?workflow_approvals.status=pending">
              <PendingWorkflowApprovals>
                <BellIcon color="white" />
                <PendingWorkflowApprovalBadge
                  id="toolbar-workflow-approval-badge"
                  isRead
                >
                  {pendingApprovalsCount}
                </PendingWorkflowApprovalBadge>
              </PendingWorkflowApprovals>
            </Link>
          </PageHeaderToolsItem>
        </Tooltip>
        <PageHeaderToolsItem>
          <Dropdown
            isPlain
            isOpen={isHelpOpen}
            position={DropdownPosition.right}
            onSelect={handleHelpSelect}
            toggle={
              <DropdownToggle
                onToggle={setIsHelpOpen}
                aria-label={i18n._(t`Info`)}
              >
                <QuestionCircleIcon />
              </DropdownToggle>
            }
            dropdownItems={[
              <DropdownItem
                key="help"
                target="_blank"
                href={`${getDocsBaseUrl(config)}/html/userguide/index.html`}
              >
                {i18n._(t`Help`)}
              </DropdownItem>,
              <DropdownItem
                key="about"
                component="button"
                isDisabled={isAboutDisabled}
                onClick={onAboutClick}
              >
                {i18n._(t`About`)}
              </DropdownItem>,
            ]}
          />
        </PageHeaderToolsItem>
        <Tooltip position="left" content={<div>{i18n._(t`User`)}</div>}>
          <PageHeaderToolsItem>
            <Dropdown
              id="toolbar-user-dropdown"
              isPlain
              isOpen={isUserOpen}
              position={DropdownPosition.right}
              onSelect={handleUserSelect}
              toggle={
                <DropdownToggle onToggle={setIsUserOpen}>
                  <UserIcon />
                  {loggedInUser && (
                    <span style={{ marginLeft: '10px' }}>
                      {loggedInUser.username}
                    </span>
                  )}
                </DropdownToggle>
              }
              dropdownItems={[
                <DropdownItem
                  key="user"
                  aria-label={i18n._(t`User details`)}
                  href={
                    loggedInUser
                      ? `/#/users/${loggedInUser.id}/details`
                      : '/#/home'
                  }
                >
                  {i18n._(t`User Details`)}
                </DropdownItem>,
                <DropdownItem
                  key="logout"
                  component="button"
                  onClick={onLogoutClick}
                  id="logout-button"
                >
                  {i18n._(t`Logout`)}
                </DropdownItem>,
              ]}
            />
          </PageHeaderToolsItem>
        </Tooltip>
      </PageHeaderToolsGroup>
    </PageHeaderTools>
  );
}

PageHeaderToolbar.propTypes = {
  isAboutDisabled: PropTypes.bool,
  onAboutClick: PropTypes.func.isRequired,
  onLogoutClick: PropTypes.func.isRequired,
};

PageHeaderToolbar.defaultProps = {
  isAboutDisabled: false,
};

export default withI18n()(PageHeaderToolbar);
