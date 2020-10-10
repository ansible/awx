import React, { useState } from 'react';
import { node } from 'prop-types';
import { Popover } from '@patternfly/react-core';
import { QuestionCircleIcon as PFQuestionCircleIcon } from '@patternfly/react-icons';
import styled from 'styled-components';

const QuestionCircleIcon = styled(PFQuestionCircleIcon)`
  margin-left: 10px;
`;

function FieldTooltip({ content, ...rest }) {
  const [showTooltip, setShowTooltip] = useState(false);
  if (!content) {
    return null;
  }
  return (
    <Popover
      bodyContent={content}
      isVisible={showTooltip}
      hideOnOutsideClick
      shouldClose={() => setShowTooltip(false)}
      {...rest}
    >
      <QuestionCircleIcon onClick={() => setShowTooltip(!showTooltip)} />
    </Popover>
  );
}
FieldTooltip.propTypes = {
  content: node,
};
FieldTooltip.defaultProps = {
  content: null,
};

export default FieldTooltip;
