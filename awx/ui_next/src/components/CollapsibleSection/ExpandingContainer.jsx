import 'styled-components/macro';
import React, { useState, useEffect, useRef } from 'react';
import { bool } from 'prop-types';
import styled from 'styled-components';

const Container = styled.div`
  margin: 15px 0;
  transition: height 0.2s ease-out;
  ${props => props.hideOverflow && `overflow: hidden;`}
`;

function ExpandingContainer({ isExpanded, children }) {
  const [contentHeight, setContentHeight] = useState(0);
  const [hideOverflow, setHideOverflow] = useState(!isExpanded);
  const ref = useRef(null);
  useEffect(() => {
    ref.current.addEventListener('transitionend', () => {
      setHideOverflow(!isExpanded);
    });
  });
  useEffect(() => {
    setContentHeight(ref.current.scrollHeight);
  }, [setContentHeight, children]);
  const height = isExpanded ? contentHeight : '0';
  return (
    <Container
      ref={ref}
      css={`
        height: ${height}px;
      `}
      hideOverflow={!isExpanded || hideOverflow}
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
