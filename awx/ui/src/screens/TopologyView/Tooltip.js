/* eslint-disable i18next/no-literal-string,
jsx-a11y/anchor-is-valid,
jsx-a11y/click-events-have-key-events,
jsx-a11y/no-static-element-interactions */

import React from 'react';
import styled from 'styled-components';
import {
  Button as PFButton,
  DescriptionList as PFDescriptionList,
  DescriptionListTerm,
  DescriptionListGroup as PFDescriptionListGroup,
  DescriptionListDescription,
  Divider,
  TextContent,
  Text as PFText,
  TextVariants,
} from '@patternfly/react-core';
import StatusLabel from 'components/StatusLabel';

const Wrapper = styled.div`
  position: absolute;
  top: -20px;
  right: 0;
  padding: 10px;
  width: 20%;
  background-color: rgba(255, 255, 255, 0.85);
`;
const Button = styled(PFButton)`
  width: 20px;
  height: 20px;
  border-radius: 10px;
  padding: 0;
  font-size: 11px;
`;
const DescriptionList = styled(PFDescriptionList)`
  gap: 0;
`;
const DescriptionListGroup = styled(PFDescriptionListGroup)`
  align-items: center;
  margin-top: 10px;
`;
const Text = styled(PFText)`
  margin: 10px 0 5px;
`;
function Tooltip({
  isNodeSelected,
  renderNodeIcon,
  nodeDetail,
  redirectToDetailsPage,
}) {
  return (
    <Wrapper class="tooltip" data-cy="tooltip">
      {isNodeSelected === false ? (
        <TextContent>
          <Text
            component={TextVariants.small}
            style={{ 'font-weight': 'bold', color: 'black' }}
          >
            Details
          </Text>
          <Divider component="div" />
          <Text component={TextVariants.small}>
            Click on a node icon to display the details.
          </Text>
        </TextContent>
      ) : (
        <>
          <TextContent>
            <Text
              component={TextVariants.small}
              style={{ 'font-weight': 'bold', color: 'black' }}
            >
              Details
            </Text>
            <Divider component="div" />
          </TextContent>
          <DescriptionList isHorizontal isFluid>
            <DescriptionListGroup>
              <DescriptionListTerm>
                <Button variant="primary" isSmall>
                  {renderNodeIcon()}
                </Button>
              </DescriptionListTerm>
              <DescriptionListDescription>
                <a onClick={redirectToDetailsPage}>{nodeDetail.hostname}</a>
              </DescriptionListDescription>
            </DescriptionListGroup>
            <DescriptionListGroup>
              <DescriptionListTerm>Type</DescriptionListTerm>
              <DescriptionListDescription>
                {nodeDetail.node_type} node
              </DescriptionListDescription>
            </DescriptionListGroup>
            <DescriptionListGroup>
              <DescriptionListTerm>Status</DescriptionListTerm>
              <DescriptionListDescription>
                <StatusLabel status={nodeDetail.node_state} />
              </DescriptionListDescription>
            </DescriptionListGroup>
          </DescriptionList>
        </>
      )}
    </Wrapper>
  );
}

export default Tooltip;
