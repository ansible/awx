import React, { useState } from 'react';
import { node, string } from 'prop-types';
import { Button as _Button, Popover } from '@patternfly/react-core';
import { OutlinedQuestionCircleIcon } from '@patternfly/react-icons';
import styled from 'styled-components';

const Button = styled(_Button)`
  --pf-c-button--PaddingTop: 0;
  --pf-c-button--PaddingBottom: 0;
`;

function DetailPopover({ header, content, id }) {
  const [showPopover, setShowPopover] = useState(false);
  if (!content) {
    return null;
  }
  return (
    <Popover
      bodyContent={content}
      headerContent={header}
      hideOnOutsideClick
      id={id}
      isVisible={showPopover}
      shouldClose={() => setShowPopover(false)}
    >
      <Button
        onClick={() => setShowPopover(!showPopover)}
        variant="plain"
        aria-haspopup="true"
        aria-expanded={showPopover}
      >
        <OutlinedQuestionCircleIcon
          onClick={() => setShowPopover(!showPopover)}
        />
      </Button>
    </Popover>
  );
}

DetailPopover.propTypes = {
  content: node,
  header: node,
  id: string,
};
DetailPopover.defaultProps = {
  content: null,
  header: null,
  id: 'detail-popover',
};

export default DetailPopover;
