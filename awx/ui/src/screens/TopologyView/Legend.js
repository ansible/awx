/* eslint i18next/no-literal-string: "off" */
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
  ExclamationIcon,
  CheckIcon,
  OutlinedClockIcon,
  PlusIcon,
  MinusIcon,
} from '@patternfly/react-icons';

const Wrapper = styled.div`
  position: absolute;
  left: 0;
  padding: 0 10px;
  min-width: 150px;
  background-color: rgba(255, 255, 255, 0.85);
  overflow: auto;
  height: 100%;
`;
const Button = styled(PFButton)`
  &&& {
    width: 20px;
    height: 20px;
    border-radius: 10px;
    padding: 0;
    font-size: 11px;
    background-color: white;
    border: 1px solid #ccc;
    color: black;
  }
`;
const DescriptionListDescription = styled(PFDescriptionListDescription)`
  font-size: 11px;
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
          style={{ fontWeight: 'bold', color: 'black', marginTop: 0 }}
        >
          {t`Legend`}
        </Text>
        <Divider component="div" />
        <Text component={TextVariants.small}>{t`Node types`}</Text>
      </TextContent>
      <DescriptionList isHorizontal isFluid>
        <DescriptionListGroup>
          <DescriptionListTerm>
            <Button isSmall>C</Button>
          </DescriptionListTerm>
          <DescriptionListDescription>{t`Control node`}</DescriptionListDescription>
        </DescriptionListGroup>
        <DescriptionListGroup>
          <DescriptionListTerm>
            <Button variant="primary" isSmall>
              Ex
            </Button>
          </DescriptionListTerm>
          <DescriptionListDescription>
            {t`Execution node`}
          </DescriptionListDescription>
        </DescriptionListGroup>
        <DescriptionListGroup>
          <DescriptionListTerm>
            <Button variant="primary" isSmall>
              Hy
            </Button>
          </DescriptionListTerm>
          <DescriptionListDescription>{t`Hybrid node`}</DescriptionListDescription>
        </DescriptionListGroup>
        <DescriptionListGroup>
          <DescriptionListTerm>
            <Button variant="primary" isSmall>
              h
            </Button>
          </DescriptionListTerm>
          <DescriptionListDescription>{t`Hop node`}</DescriptionListDescription>
        </DescriptionListGroup>
      </DescriptionList>
      <TextContent>
        <Text component={TextVariants.small}>{t`Node state types`}</Text>
      </TextContent>
      <DescriptionList isHorizontal isFluid>
        <DescriptionListGroup>
          <DescriptionListTerm>
            <Button
              icon={
                <CheckIcon
                  style={{ fill: 'white', marginLeft: '2px', marginTop: '3px' }}
                />
              }
              isSmall
              style={{ backgroundColor: '#3E8635' }}
            />
          </DescriptionListTerm>
          <DescriptionListDescription>{t`Ready`}</DescriptionListDescription>
        </DescriptionListGroup>
        <DescriptionListGroup>
          <DescriptionListTerm>
            <Button
              icon={
                <OutlinedClockIcon
                  style={{ fill: 'white', marginLeft: '3px', marginTop: '3px' }}
                />
              }
              isSmall
              style={{ backgroundColor: '#0066CC' }}
            />
          </DescriptionListTerm>
          <DescriptionListDescription>{t`Installed`}</DescriptionListDescription>
        </DescriptionListGroup>
        <DescriptionListGroup>
          <DescriptionListTerm>
            <Button
              icon={
                <PlusIcon
                  style={{ fill: 'white', marginLeft: '3px', marginTop: '3px' }}
                />
              }
              isSmall
              style={{ backgroundColor: '#6A6E73' }}
            />
          </DescriptionListTerm>
          <DescriptionListDescription>{t`Provisioning`}</DescriptionListDescription>
        </DescriptionListGroup>
        <DescriptionListGroup>
          <DescriptionListTerm>
            <Button
              icon={
                <MinusIcon
                  style={{ fill: 'white', marginLeft: '3px', marginTop: '3px' }}
                />
              }
              isSmall
              style={{ backgroundColor: '#6A6E73' }}
            />
          </DescriptionListTerm>
          <DescriptionListDescription>{t`Deprovisioning`}</DescriptionListDescription>
        </DescriptionListGroup>
        <DescriptionListGroup>
          <DescriptionListTerm>
            <Button
              icon={
                <ExclamationIcon
                  style={{ fill: 'white', marginLeft: '3px', marginTop: '3px' }}
                />
              }
              isSmall
              style={{ backgroundColor: '#C9190B' }}
            />
          </DescriptionListTerm>
          <DescriptionListDescription>{t`Error`}</DescriptionListDescription>
        </DescriptionListGroup>
        <DescriptionListGroup>
          <DescriptionListTerm>
            <svg width="20" height="20" xmlns="http://www.w3.org/2000/svg">
              <circle
                r="9"
                cx="10"
                cy="10"
                fill="transparent"
                strokeWidth="1px"
                stroke="#ccc"
              />
              <text
                x="10"
                y="10"
                textAnchor="middle"
                dominantBaseline="central"
                fill="black"
                fontSize="11px"
                fontFamily="inherit"
                fontWeight="400"
              >
                C
              </text>
            </svg>
          </DescriptionListTerm>
          <DescriptionListDescription>{t`Enabled`}</DescriptionListDescription>
        </DescriptionListGroup>
        <DescriptionListGroup>
          <DescriptionListTerm>
            <svg width="20" height="20" xmlns="http://www.w3.org/2000/svg">
              <circle
                r="9"
                cx="10"
                cy="10"
                fill="transparent"
                strokeDasharray="5"
                strokeWidth="1px"
                stroke="#ccc"
              />
              <text
                x="10"
                y="10"
                textAnchor="middle"
                dominantBaseline="central"
                fill="black"
                fontSize="11px"
                fontFamily="inherit"
                fontWeight="400"
              >
                C
              </text>
            </svg>
          </DescriptionListTerm>
          <DescriptionListDescription>{t`Disabled`}</DescriptionListDescription>
        </DescriptionListGroup>
      </DescriptionList>
      <TextContent>
        <Text component={TextVariants.small}>{t`Link state types`}</Text>
      </TextContent>
      <DescriptionList isHorizontal isFluid>
        <DescriptionListGroup>
          <DescriptionListTerm>
            <svg width="20" height="15" xmlns="http://www.w3.org/2000/svg">
              <line
                x1="0"
                y1="9"
                x2="20"
                y2="9"
                stroke="#6A6E73"
                strokeWidth="4"
              />
            </svg>
          </DescriptionListTerm>
          <DescriptionListDescription>{t`Established`}</DescriptionListDescription>
        </DescriptionListGroup>
        <DescriptionListGroup>
          <DescriptionListTerm>
            <svg width="20" height="15" xmlns="http://www.w3.org/2000/svg">
              <line
                x1="0"
                y1="9"
                x2="20"
                y2="9"
                stroke="#ccc"
                strokeWidth="4"
                strokeDasharray="6"
              />
            </svg>
          </DescriptionListTerm>
          <DescriptionListDescription>{t`Disconnected`}</DescriptionListDescription>
        </DescriptionListGroup>
        <DescriptionListGroup>
          <DescriptionListTerm>
            <svg width="20" height="15" xmlns="http://www.w3.org/2000/svg">
              <line
                x1="0"
                y1="9"
                x2="20"
                y2="9"
                stroke="#3E8635"
                strokeWidth="4"
                strokeDasharray="6"
              />
            </svg>
          </DescriptionListTerm>
          <DescriptionListDescription>{t`Adding`}</DescriptionListDescription>
        </DescriptionListGroup>
        <DescriptionListGroup>
          <DescriptionListTerm>
            <svg width="20" height="15" xmlns="http://www.w3.org/2000/svg">
              <line
                x1="0"
                y1="9"
                x2="20"
                y2="9"
                stroke="#C9190B"
                strokeWidth="4"
                strokeDasharray="6"
              />
            </svg>
          </DescriptionListTerm>
          <DescriptionListDescription>{t`Removing`}</DescriptionListDescription>
        </DescriptionListGroup>
      </DescriptionList>
    </Wrapper>
  );
}

export default Legend;
