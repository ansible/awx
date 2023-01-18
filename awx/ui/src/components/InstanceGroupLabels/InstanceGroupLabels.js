import React from 'react';
import { arrayOf, bool, number, shape, string } from 'prop-types';

import { Label, LabelGroup } from '@patternfly/react-core';
import { Link } from 'react-router-dom';

function InstanceGroupLabels({ labels, isLinkable }) {
  const buildLinkURL = (isContainerGroup) =>
    isContainerGroup
      ? '/instance_groups/container_group/'
      : '/instance_groups/';
  return (
    <LabelGroup numLabels={5}>
      {labels.map(({ id, name, is_container_group }) =>
        isLinkable ? (
          <Label
            color="blue"
            key={id}
            render={({ className, content, componentRef }) => (
              <Link
                className={className}
                innerRef={componentRef}
                to={`${buildLinkURL(is_container_group)}${id}/details`}
              >
                {content}
              </Link>
            )}
          >
            {name}
          </Label>
        ) : (
          <Label color="blue" key={id}>
            {name}
          </Label>
        )
      )}
    </LabelGroup>
  );
}

InstanceGroupLabels.propTypes = {
  labels: arrayOf(shape({ id: number.isRequired, name: string.isRequired }))
    .isRequired,
  isLinkable: bool,
};

InstanceGroupLabels.defaultProps = { isLinkable: false };

export default InstanceGroupLabels;
