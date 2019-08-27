import React, { useState, useEffect, useRef } from 'react';
import { bool } from 'prop-types';
import styled from 'styled-components';

const Container = styled.div`
  margin: 15px 0;
  transition: all 0.2s ease-out;
  ${props => !props.isExpanded && `
    overflow: hidden;
  `}
`;

function ExpandingContainer({ isExpanded, children }) {
  const [contentHeight, setContentHeight] = useState(0);
  const ref = useRef(null);
  useEffect(() => {
    setContentHeight(ref.current.scrollHeight);
  });
  const height = isExpanded ? contentHeight : '0';
  return (
    <Container
      ref={ref}
      css={`
        height: ${height}px;
      `}
      isExpanded={isExpanded}
    >
      {children}
    </Container>
  );
}
ExpandingContainer.propTypes = {
  isExpanded: bool,
};
ExpandingContainer.defaultProps = {
  isExpanded: false,
};

export default ExpandingContainer;
