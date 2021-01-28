import React from 'react';
import { node, bool, string } from 'prop-types';
import { TextListItem, TextListItemVariants } from '@patternfly/react-core';
import styled from 'styled-components';
import Popover from '../Popover';

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

const DetailValue = styled(
  ({ fullWidth, isEncrypted, isNotConfigured, ...props }) => (
    <TextListItem {...props} />
  )
)`
  word-break: break-all;
  ${props =>
    props.fullWidth &&
    `
    grid-column: 2 / -1;
  `}
  ${props =>
    (props.isEncrypted || props.isNotConfigured) &&
    `
    color: var(--pf-global--Color--400);
  `}
`;

const Detail = ({
  id,
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
  id: string,
  label: node.isRequired,
  value: node,
  fullWidth: bool,
  alwaysVisible: bool,
  helpText: string,
};
Detail.defaultProps = {
  id: null,
  value: null,
  fullWidth: false,
  alwaysVisible: false,
  helpText: null,
};

export default Detail;
export { DetailName };
export { DetailValue };
