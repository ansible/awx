import React from 'react';
import PropTypes from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { AboutModal } from '@patternfly/react-core';

import { BrandName } from '../../variables';

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
  const copyright = i18n._(t`Copyright`);
  const redHatInc = i18n._(t`Red Hat, Inc.`);

  return (
    <AboutModal
      isOpen={isOpen}
      onClose={onClose}
      productName={`Ansible ${BrandName}`}
      trademark={`${copyright} ${new Date().getFullYear()} ${redHatInc}`}
      brandImageSrc="/static/media/logo-header.svg"
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
