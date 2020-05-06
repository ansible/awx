import React, { useState } from 'react';
import { bool, string } from 'prop-types';
import styled from 'styled-components';
import { Button } from '@patternfly/react-core';
import { AngleRightIcon } from '@patternfly/react-icons';
import omitProps from '../../util/omitProps';
import ExpandingContainer from './ExpandingContainer';

// Make button findable by tests
Button.displayName = 'Button';

const Toggle = styled.div`
  display: flex;

  hr {
    margin-left: 20px;
    flex: 1 1 auto;
    align-self: center;
    border: 0;
    border-bottom: 1px solid var(--pf-global--BorderColor--300);
  }
`;

const Arrow = styled(omitProps(AngleRightIcon, 'isExpanded'))`
  margin-right: -5px;
  margin-left: 5px;
  transition: transform 0.1s ease-out;
  transform-origin: 50% 50%;
  ${props => props.isExpanded && `transform: rotate(90deg);`}
`;

function CollapsibleSection({ label, startExpanded, children }) {
  const [isExpanded, setIsExpanded] = useState(startExpanded);
  const toggle = () => setIsExpanded(!isExpanded);

  return (
    <div>
      <Toggle>
        <Button onClick={toggle}>
          {label} <Arrow isExpanded={isExpanded} />
        </Button>
        <hr />
      </Toggle>
      <ExpandingContainer isExpanded={isExpanded}>
        {children}
      </ExpandingContainer>
    </div>
  );
}
CollapsibleSection.propTypes = {
  label: string.isRequired,
  startExpanded: bool,
};
CollapsibleSection.defaultProps = {
  startExpanded: false,
};

export default CollapsibleSection;
