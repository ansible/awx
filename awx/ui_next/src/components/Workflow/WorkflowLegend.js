import React, { useContext } from 'react';

import { t } from '@lingui/macro';
import styled from 'styled-components';
import {
  ExclamationTriangleIcon,
  PauseIcon,
  TimesIcon,
} from '@patternfly/react-icons';
import { WorkflowDispatchContext } from 'contexts/Workflow';

const Wrapper = styled.div`
  background-color: white;
  border: 1px solid #c7c7c7;
  margin-left: 20px;
  min-width: 100px;
  position: relative;
`;

const Header = styled.div`
  border-bottom: 1px solid #c7c7c7;
  padding: 10px;
  position: relative;
`;

const Legend = styled.ul`
  padding: 5px 10px;

  li {
    align-items: center;
    display: flex;
    padding: 5px 0px;
  }
`;

const NodeTypeLetter = styled.div`
  background-color: #393f43;
  border-radius: 50%;
  color: white;
  font-size: 10px;
  height: 20px;
  line-height: 20px;
  margin-right: 10px;
  text-align: center;
  width: 20px;
`;

const StyledExclamationTriangleIcon = styled(ExclamationTriangleIcon)`
  color: #f0ad4d;
  height: 20px;
  margin-right: 10px;
  width: 20px;
`;

const Link = styled.div`
  height: 5px;
  margin-right: 10px;
  width: 20px;
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

const Close = styled(TimesIcon)`
  cursor: pointer;
  position: absolute;
  right: 10px;
  top: 15px;
`;

function WorkflowLegend() {
  const dispatch = useContext(WorkflowDispatchContext);

  return (
    <Wrapper>
      <Header>
        <b>{t`Legend`}</b>
        <Close onClick={() => dispatch({ type: 'TOGGLE_LEGEND' })} />
      </Header>
      <Legend>
        <li>
          <NodeTypeLetter>JT</NodeTypeLetter>
          <span>{t`Job Template`}</span>
        </li>
        <li>
          <NodeTypeLetter>W</NodeTypeLetter>
          <span>{t`Workflow`}</span>
        </li>
        <li>
          <NodeTypeLetter>I</NodeTypeLetter>
          <span>{t`Inventory Sync`}</span>
        </li>
        <li>
          <NodeTypeLetter>P</NodeTypeLetter>
          <span>{t`Project Sync`}</span>
        </li>
        <li>
          <NodeTypeLetter>M</NodeTypeLetter>
          <span>{t`Management Job`}</span>
        </li>
        <li>
          <NodeTypeLetter>
            <PauseIcon />
          </NodeTypeLetter>
          <span>{t`Approval`}</span>
        </li>
        <li>
          <StyledExclamationTriangleIcon />
          <span>{t`Warning`}</span>
        </li>
        <li>
          <SuccessLink />
          <span>{t`On Success`}</span>
        </li>
        <li>
          <FailureLink />
          <span>{t`On Failure`}</span>
        </li>
        <li>
          <AlwaysLink />
          <span>{t`Always`}</span>
        </li>
      </Legend>
    </Wrapper>
  );
}

export default WorkflowLegend;
