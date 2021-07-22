import 'styled-components/macro';
import React, { useContext } from 'react';

import { t } from '@lingui/macro';
import { Button as PFButton } from '@patternfly/react-core';
import styled from 'styled-components';
import { WorkflowDispatchContext } from 'contexts/Workflow';

const Button = styled(PFButton)`
  && {
    background-color: #5cb85c;
    padding: 5px 8px;
    --pf-global--FontSize--md: 14px;
    margin-top: 20px;
  }
`;

const StartPanel = styled.div`
  background-color: white;
  border: 1px solid #c7c7c7;
  padding: 60px 80px;
  text-align: center;
`;

const StartPanelWrapper = styled.div`
  align-items: center;
  background-color: #f6f6f6;
  display: flex;
  height: 100%;
  justify-content: center;
`;

function VisualizerStartScreen({ readOnly }) {
  const dispatch = useContext(WorkflowDispatchContext);
  return (
    <div css="flex: 1">
      <StartPanelWrapper>
        <StartPanel>
          {readOnly ? (
            <p>{t`This workflow does not have any nodes configured.`}</p>
          ) : (
            <>
              <p>{t`Please click the Start button to begin.`}</p>
              <Button
                ouiaId="visualizer-start-button"
                id="visualizer-start"
                aria-label={t`Start`}
                onClick={() =>
                  dispatch({ type: 'START_ADD_NODE', sourceNodeId: 1 })
                }
                variant="primary"
              >
                {t`Start`}
              </Button>
            </>
          )}
        </StartPanel>
      </StartPanelWrapper>
    </div>
  );
}

export default VisualizerStartScreen;
