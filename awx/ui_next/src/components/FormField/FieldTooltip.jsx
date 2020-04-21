import React from 'react';
import { node } from 'prop-types';
import { Tooltip } from '@patternfly/react-core';
import { QuestionCircleIcon as PFQuestionCircleIcon } from '@patternfly/react-icons';
import styled from 'styled-components';

const QuestionCircleIcon = styled(PFQuestionCircleIcon)`
  margin-left: 10px;
`;

function FieldTooltip({ content, ...rest }) {
  if (!content) {
    return null;
  }
  return (
    <Tooltip
      position="right"
      content={content}
      trigger="click mouseenter focus"
      {...rest}
    >
      <QuestionCircleIcon />
    </Tooltip>
  );
}
FieldTooltip.propTypes = {
  content: node,
};
FieldTooltip.defaultProps = {
  content: null,
};

export default FieldTooltip;
