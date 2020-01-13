import React from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import styled from 'styled-components';
import { ExclamationTriangleIcon, PauseIcon } from '@patternfly/react-icons';

const Wrapper = styled.div`
  border: 1px solid #c7c7c7;
  background-color: white;
  min-width: 100px;
  margin-left: 20px;
`;

const Header = styled.div`
  padding: 10px;
  border-bottom: 1px solid #c7c7c7;
`;

const Key = styled.ul`
  padding: 5px 10px;

  li {
    padding: 5px 0px;
    display: flex;
    align-items: center;
  }
`;

const NodeTypeLetter = styled.div`
  font-size: 10px;
  color: white;
  text-align: center;
  line-height: 20px;
  background-color: #393f43;
  border-radius: 50%;
  height: 20px;
  width: 20px;
  margin-right: 10px;
`;

const StyledExclamationTriangleIcon = styled(ExclamationTriangleIcon)`
  color: #f0ad4d;
  margin-right: 10px;
  height: 20px;
  width: 20px;
`;

const Link = styled.div`
  height: 5px;
  width: 20px;
  margin-right: 10px;
`;

const SuccessLink = styled(Link)`
  background-color: #5cb85c;
`;

const FailureLink = styled(Link)`
  background-color: #d9534f;
`;

const AlwaysLink = styled(Link)`
  background-color: #337ab7;
`;

function VisualizerKey({ i18n }) {
  return (
    <Wrapper>
      <Header>
        <b>{i18n._(t`Key`)}</b>
      </Header>
      <Key>
        <li>
          <NodeTypeLetter>JT</NodeTypeLetter>
          <span>{i18n._(t`Job Template`)}</span>
        </li>
        <li>
          <NodeTypeLetter>W</NodeTypeLetter>
          <span>{i18n._(t`Workflow`)}</span>
        </li>
        <li>
          <NodeTypeLetter>I</NodeTypeLetter>
          <span>{i18n._(t`Inventory Sync`)}</span>
        </li>
        <li>
          <NodeTypeLetter>P</NodeTypeLetter>
          <span>{i18n._(t`Project Sync`)}</span>
        </li>
        <li>
          <NodeTypeLetter>
            <PauseIcon />
          </NodeTypeLetter>
          <span>{i18n._(t`Approval`)}</span>
        </li>
        <li>
          <StyledExclamationTriangleIcon />
          <span>{i18n._(t`Warning`)}</span>
        </li>
        <li>
          <SuccessLink />
          <span>{i18n._(t`On Success`)}</span>
        </li>
        <li>
          <FailureLink />
          <span>{i18n._(t`On Failure`)}</span>
        </li>
        <li>
          <AlwaysLink />
          <span>{i18n._(t`Always`)}</span>
        </li>
      </Key>
    </Wrapper>
  );
}

export default withI18n()(VisualizerKey);
