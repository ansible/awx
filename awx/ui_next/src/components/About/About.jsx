import React from 'react';
import PropTypes from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { AboutModal } from '@patternfly/react-core';

import { BrandName } from '../../variables';
import brandLogoImg from './brand-logo.svg';

function About({ version, isOpen, onClose, i18n }) {
  const createSpeechBubble = () => {
    let text = `${BrandName} ${version}`;
    let top = '';
    let bottom = '';

    for (let i = 0; i < text.length; i++) {
      top += '_';
      bottom += '-';
    }

    top = ` __${top}__ \n`;
    text = `<  ${text}  >\n`;
    bottom = ` --${bottom}-- `;

    return top + text + bottom;
  };

  const speechBubble = createSpeechBubble();

  return (
    <AboutModal
      isOpen={isOpen}
      onClose={onClose}
      productName={`Ansible ${BrandName}`}
      trademark={i18n._(t`Copyright 2019 Red Hat, Inc.`)}
      brandImageSrc={brandLogoImg}
      brandImageAlt={i18n._(t`Brand Image`)}
    >
      <pre>
        {speechBubble}
        {`
          \\
          \\   ^__^
              (oo)\\_______
              (__)      A )\\
                  ||----w |
                  ||     ||
                    `}
      </pre>
    </AboutModal>
  );
}

About.propTypes = {
  isOpen: PropTypes.bool,
  onClose: PropTypes.func.isRequired,
  version: PropTypes.string,
};

About.defaultProps = {
  isOpen: false,
  version: null,
};

export default withI18n()(About);
