import React from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Button as PFButton } from '@patternfly/react-core';
import styled from 'styled-components';

const Button = styled(PFButton)`
  && {
    background-color: #5cb85c;
    padding: 5px 8px;
    --pf-global--FontSize--md: 14px;
    margin-top: 20px;
  }
`;

const StartPanel = styled.div`
  padding: 60px 80px;
  border: 1px solid #c7c7c7;
  background-color: white;
  color: var(--pf-global--Color--200);
  text-align: center;
`;

const StartPanelWrapper = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  background-color: #f6f6f6;
`;

function StartScreen({ i18n }) {
  return (
    <div css="flex: 1">
      <StartPanelWrapper>
        <StartPanel>
          <p>{i18n._(t`Please click the Start button to begin.`)}</p>
          <Button variant="primary" aria-label={i18n._(t`Start`)}>
            {i18n._(t`Start`)}
          </Button>
        </StartPanel>
      </StartPanelWrapper>
    </div>
  );
}

export default withI18n()(StartScreen);
