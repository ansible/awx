import React from 'react';
import { node, bool } from 'prop-types';
import { TextListItem, TextListItemVariants } from '@patternfly/react-core';
import styled from 'styled-components';

const DetailName = styled(({ fullWidth, ...props }) => (
  <TextListItem {...props} />
))`
  font-weight: var(--pf-global--FontWeight--bold);
  ${props =>
    props.fullWidth &&
    `
    grid-column: 1;
  `}
`;

const DetailValue = styled(({ fullWidth, isEncrypted, ...props }) => (
  <TextListItem {...props} />
))`
  word-break: break-all;
  ${props =>
    props.fullWidth &&
    `
    grid-column: 2 / -1;
  `}
  ${props =>
    props.isEncrypted &&
    `
    text-transform: uppercase
    color: var(--pf-global--Color--400);
  `}
`;

const Detail = ({
  label,
  value,
  fullWidth,
  className,
  dataCy,
  alwaysVisible,
  isEncrypted,
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
      >
        {label}
      </DetailName>
      <DetailValue
        className={className}
        component={TextListItemVariants.dd}
        fullWidth={fullWidth}
        data-cy={valueCy}
        isEncrypted={isEncrypted}
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
};
Detail.defaultProps = {
  value: null,
  fullWidth: false,
  alwaysVisible: false,
};

export default Detail;
export { DetailName };
export { DetailValue };
