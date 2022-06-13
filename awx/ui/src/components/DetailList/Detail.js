import React from 'react';

import { oneOfType, node, bool, string } from 'prop-types';
import { TextListItem, TextListItemVariants } from '@patternfly/react-core';
import styled from 'styled-components';
import Popover from '../Popover';

const DetailName = styled(({ fullWidth, ...props }) => (
  <TextListItem {...props} />
))`
  font-weight: var(--pf-global--FontWeight--bold);
  ${(props) =>
    props.fullWidth &&
    `
    grid-column: 1;
  `}
`;

const DetailValue = styled(
  ({ fullWidth, isEncrypted, isNotConfigured, ...props }) => (
    <TextListItem {...props} />
  )
)`
  overflow-wrap: break-word;
  ${(props) =>
    props.fullWidth &&
    `
    grid-column: 2 / -1;
  `}
  ${(props) =>
    (props.isEncrypted || props.isNotConfigured) &&
    `
    color: var(--pf-global--disabled-color--100);
  `}
`;

const Detail = ({
  label,
  value,
  fullWidth,
  className,
  dataCy,
  alwaysVisible,
  helpText,
  isEncrypted,
  isNotConfigured,
}) => {
  if (!value && typeof value !== 'number' && !alwaysVisible) {
    return null;
  }

  const labelCy = dataCy ? `${dataCy}-label` : null;
  const valueCy = dataCy ? `${dataCy}-value` : null;

  return (
    <>
      <DetailName
        className={className}
        component={TextListItemVariants.dt}
        fullWidth={fullWidth}
        data-cy={labelCy}
        id={dataCy}
      >
        {label}
        {helpText && <Popover header={label} content={helpText} id={dataCy} />}
      </DetailName>
      <DetailValue
        className={className}
        component={TextListItemVariants.dd}
        fullWidth={fullWidth}
        data-cy={valueCy}
        isEncrypted={isEncrypted}
        isNotConfigured={isNotConfigured}
      >
        {value}
      </DetailValue>
    </>
  );
};
Detail.propTypes = {
  label: node.isRequired,
  value: node,
  fullWidth: bool,
  alwaysVisible: bool,
  helpText: oneOfType([string, node]),
};
Detail.defaultProps = {
  value: null,
  fullWidth: false,
  alwaysVisible: false,
  helpText: null,
};

export default Detail;
export { DetailName };
export { DetailValue };
