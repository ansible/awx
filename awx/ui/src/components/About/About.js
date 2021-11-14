import React from 'react';
import PropTypes from 'prop-types';
import { t } from '@lingui/macro';
import { AboutModal } from '@patternfly/react-core';
import useBrandName from 'hooks/useBrandName';

function About({ version, isOpen, onClose }) {
  const brandName = useBrandName();

  const createSpeechBubble = () => {
    let text = '';
    if (typeof brandName === 'string' && brandName.length > 0) {
      text =
        brandName.indexOf('AWX') === -1
          ? `${brandName} Controller ${version}`
          : `${brandName} ${version}`;
    }

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
  const copyright = t`Copyright`;
  const redHatInc = t`Red Hat, Inc.`;

  return (
    <AboutModal
      isOpen={isOpen}
      onClose={onClose}
      productName={brandName}
      trademark={`${copyright} ${new Date().getFullYear()} ${redHatInc}`}
      brandImageSrc="static/media/logo-header.svg"
      brandImageAlt={t`Brand Image`}
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

export default About;
