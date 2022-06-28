import React from 'react';
import { AngleLeftIcon, AngleRightIcon } from '@patternfly/react-icons';
import { Tab, Tabs, TabTitleIcon, TabTitleText } from '@patternfly/react-core';
import styled from 'styled-components';

const Wrapper = styled(Tabs)`
  display: flex;
  justify-content: flex-end;
  flex: 1;
`;

function WorkflowOutputNavigation({ job }) {
  console.log(job);
  if (!job) {
    return null;
  }
  console.log(job);
  return (
    <Wrapper>
      <Tab
        title={
          <>
            <TabTitleIcon>
              <AngleLeftIcon />
            </TabTitleIcon>
            <TabTitleText>{job.name}</TabTitleText>
            <TabTitleIcon>
              <AngleRightIcon />
            </TabTitleIcon>
          </>
        }
      />
    </Wrapper>
  );
}

export default WorkflowOutputNavigation;
