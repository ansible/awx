import React from 'react';
import { t } from '@lingui/macro';
import styled from 'styled-components';
import {
  Button as PFButton,
  DescriptionList as PFDescriptionList,
  DescriptionListTerm,
  DescriptionListGroup as PFDescriptionListGroup,
  DescriptionListDescription as PFDescriptionListDescription,
  Divider,
  TextContent,
  Text as PFText,
  TextVariants,
} from '@patternfly/react-core';

import {
  ExclamationIcon as PFExclamationIcon,
  CheckIcon as PFCheckIcon,
} from '@patternfly/react-icons';

const Wrapper = styled.div`
  position: absolute;
  top: -20px;
  left: 0;
  padding: 10px;
  width: 150px;
  background-color: rgba(255, 255, 255, 0.85);
`;
const Button = styled(PFButton)`
  width: 20px;
  height: 20px;
  border-radius: 10px;
  padding: 0;
  font-size: 11px;
`;
const DescriptionListDescription = styled(PFDescriptionListDescription)`
  font-size: 11px;
`;
const ExclamationIcon = styled(PFExclamationIcon)`
  fill: white;
  margin-left: 2px;
`;
const CheckIcon = styled(PFCheckIcon)`
  fill: white;
  margin-left: 2px;
`;
const DescriptionList = styled(PFDescriptionList)`
  gap: 7px;
`;
const DescriptionListGroup = styled(PFDescriptionListGroup)`
  align-items: center;
`;
const Text = styled(PFText)`
  margin: 10px 0 5px;
`;

function Legend() {
  return (
    <Wrapper className="legend" data-cy="legend">
      <TextContent>
        <Text
          component={TextVariants.small}
          style={{ fontWeight: 'bold', color: 'black' }}
        >
          {t`Legend`}
        </Text>
        <Divider component="div" />
        <Text component={TextVariants.small}>{t`Node types`}</Text>
      </TextContent>
      <DescriptionList isHorizontal isFluid>
        <DescriptionListGroup>
          <DescriptionListTerm>
            <Button variant="primary" isSmall>
              {t`C`}
            </Button>
          </DescriptionListTerm>
          <DescriptionListDescription>{t`Control node`}</DescriptionListDescription>
        </DescriptionListGroup>
        <DescriptionListGroup>
          <DescriptionListTerm>
            <Button variant="primary" isSmall>
              {t`Ex`}
            </Button>
          </DescriptionListTerm>
          <DescriptionListDescription>
            {t`Execution node`}
          </DescriptionListDescription>
        </DescriptionListGroup>
        <DescriptionListGroup>
          <DescriptionListTerm>
            <Button variant="primary" isSmall>
              {t`Hy`}
            </Button>
          </DescriptionListTerm>
          <DescriptionListDescription>{t`Hybrid node`}</DescriptionListDescription>
        </DescriptionListGroup>
        <DescriptionListGroup>
          <DescriptionListTerm>
            <Button variant="primary" isSmall>
              {t`h`}
            </Button>
          </DescriptionListTerm>
          <DescriptionListDescription>{t`Hop node`}</DescriptionListDescription>
        </DescriptionListGroup>
      </DescriptionList>
      <TextContent>
        <Text component={TextVariants.small}>{t`Status types`}</Text>
      </TextContent>
      <DescriptionList isHorizontal isFluid>
        <DescriptionListGroup>
          <DescriptionListTerm>
            <Button
              icon={<CheckIcon />}
              isSmall
              style={{ border: '1px solid gray', backgroundColor: '#3E8635' }}
            />
          </DescriptionListTerm>
          <DescriptionListDescription>{t`Healthy`}</DescriptionListDescription>
        </DescriptionListGroup>
        <DescriptionListGroup>
          <DescriptionListTerm>
            <Button variant="danger" icon={<ExclamationIcon />} isSmall />
          </DescriptionListTerm>
          <DescriptionListDescription>{t`Error`}</DescriptionListDescription>
        </DescriptionListGroup>
        <DescriptionListGroup>
          <DescriptionListTerm>
            <Button
              isSmall
              style={{ border: '1px solid gray', backgroundColor: '#e6e6e6' }}
            />
          </DescriptionListTerm>
          <DescriptionListDescription>{t`Disabled`}</DescriptionListDescription>
        </DescriptionListGroup>
      </DescriptionList>
    </Wrapper>
  );
}

export default Legend;
