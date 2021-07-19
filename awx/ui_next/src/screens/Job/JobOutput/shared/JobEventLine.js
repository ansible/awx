import styled from 'styled-components';

export default styled.div`
  display: flex;

  &:hover {
    background-color: white;
    cursor: ${props => (props.isClickable ? 'pointer' : 'default')};
  }

  &:hover div {
    background-color: white;
  }

  &--hidden {
    display: none;
  }
  ${({ isFirst }) => (isFirst ? 'padding-top: 10px;' : '')}
`;
