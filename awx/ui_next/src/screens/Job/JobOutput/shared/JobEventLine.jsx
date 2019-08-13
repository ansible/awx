import styled from 'styled-components';

export default styled.div`
  display: flex;

  &:hover {
    background-color: white;
  }

  &:hover div {
    background-color: white;
  }

  &--hidden {
    display: none;
  }
  ${({ isFirst }) => (isFirst ? 'padding-top: 10px;' : '')}
`;
