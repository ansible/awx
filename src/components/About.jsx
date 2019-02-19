import React from 'react';
import PropTypes from 'prop-types';
import { I18n } from '@lingui/react';
import { Trans, t } from '@lingui/macro';
import {
  AboutModal,
  TextContent,
  TextList,
  TextListItem
} from '@patternfly/react-core';

import heroImg from '@patternfly/patternfly-next/assets/images/pfbg_992.jpg';
import brandImg from '../../images/tower-logo-white.svg';
import logoImg from '../../images/tower-logo-login.svg';

class About extends React.Component {
  static createSpeechBubble (version) {
    let text = `Tower ${version}`;
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
  }

  constructor (props) {
    super(props);

    this.createSpeechBubble = this.constructor.createSpeechBubble.bind(this);
  }

  render () {
    const {
      ansible_version,
      version,
      isOpen,
      onClose
    } = this.props;

    const speechBubble = this.createSpeechBubble(version);

    return (
      <I18n>
        {({ i18n }) => (
          <AboutModal
            isOpen={isOpen}
            onClose={onClose}
            productName="Ansible Tower"
            trademark={i18n._(t`Copyright 2018 Red Hat, Inc.`)}
            brandImageSrc={brandImg}
            brandImageAlt={i18n._(t`Brand Image`)}
            logoImageSrc={logoImg}
            logoImageAlt={i18n._(t`AboutModal Logo`)}
            heroImageSrc={heroImg}
          >
            <pre>
              { speechBubble }
              {`
              \\
              \\   ^__^
                  (oo)\\_______
                  (__)      A )\\
                      ||----w |
                      ||     ||
                        `}
            </pre>
            <TextContent>
              <TextList component="dl">
                <TextListItem component="dt">
                  <Trans>Ansible Version</Trans>
                </TextListItem>
                <TextListItem component="dd">{ ansible_version }</TextListItem>
              </TextList>
            </TextContent>
          </AboutModal>
        )}
      </I18n>
    );
  }
}

About.propTypes = {
  ansible_version: PropTypes.string,
  isOpen: PropTypes.bool,
  onClose: PropTypes.func.isRequired,
  version: PropTypes.string,
};

About.defaultProps = {
  ansible_version: null,
  isOpen: false,
  version: null,
};

export default About;
