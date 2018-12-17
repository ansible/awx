import React from 'react';
import { I18n } from '@lingui/react';
import { Trans, t } from '@lingui/macro';
import {
  AboutModal,
  TextContent,
  TextList,
  TextListItem } from '@patternfly/react-core';

import heroImg from '@patternfly/patternfly-next/assets/images/pfbg_992.jpg';
import brandImg from '../../images/tower-logo-white.svg';
import logoImg from '../../images/tower-logo-login.svg';

import api from '../api';
import { API_CONFIG } from '../endpoints';

class About extends React.Component {
  unmounting = false;

  constructor (props) {
    super(props);

    this.state = {
      config: {},
      error: false
    };
  }

  async componentDidMount () {
    try {
      const { data } = await api.get(API_CONFIG);
      this.safeSetState({ config: data });
    } catch (error) {
      this.safeSetState({ error });
    }
  }

  componentWillUnmount () {
    this.unmounting = true;
  }

  safeSetState = obj => !this.unmounting && this.setState(obj);

  createSpeechBubble = (version) => {
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

  handleModalToggle = () => {
    const { onAboutModalClose } = this.props;
    onAboutModalClose();
  };

  render () {
    const { isOpen } = this.props;
    const { config = {}, error } = this.state;
    const { ansible_version = 'loading', version = 'loading' } = config;

    return (
      <I18n>
        {({ i18n }) => (
          <AboutModal
            isOpen={isOpen}
            onClose={this.handleModalToggle}
            productName="Ansible Tower"
            trademark={i18n._(t`Copyright 2018 Red Hat, Inc.`)}
            brandImageSrc={brandImg}
            brandImageAlt={i18n._(t`Brand Image`)}
            logoImageSrc={logoImg}
            logoImageAlt={i18n._(t`AboutModal Logo`)}
            heroImageSrc={heroImg}
          >
            <pre>
              { this.createSpeechBubble(version) }
              {`
              \\
              \\  ^__^
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
            { error ? <div>error</div> : ''}
          </AboutModal>
        )}
      </I18n>
    );
  }
}

export default About;
