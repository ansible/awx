import React from 'react';
import { arrayOf, node, shape, string } from 'prop-types';
import DataListCell from '@components/DataListCell';
import styled from 'styled-components';

const ActionButtonCellStyled = styled(DataListCell)`
  & > ul {
    display: flex;
    li:not(:first-child) {
      margin-left: 20px;
    }
  }
`;

const ActionButtonCell = ({ ...props }) => {
  const { actions } = props;
  return (
    <ActionButtonCellStyled {...props}>
      <ul key="listActions">
        {actions.map(action => (
          <li key={action.key}>{action.content}</li>
        ))}
      </ul>
    </ActionButtonCellStyled>
  );
};
ActionButtonCell.propTypes = {
  actions: arrayOf(
    shape({
      key: string,
      content: node,
    })
  ),
};
ActionButtonCell.defaultProps = {
  actions: [],
};

export default ActionButtonCell;
