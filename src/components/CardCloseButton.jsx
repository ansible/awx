import React from 'react';
import { string } from 'prop-types';
import { Link } from 'react-router-dom';
import { Button } from '@patternfly/react-core';
import { TimesIcon } from '@patternfly/react-icons';
import { I18n } from '@lingui/react';
import { t } from '@lingui/macro';

function CardCloseButton ({ linkTo, ...props }) {
  if (linkTo) {
    return (
      <I18n>
        {({ i18n }) => (
          <Link
            className="pf-c-button pf-c-card__close"
            aria-label={i18n._(t`Close`)}
            title={i18n._(t`Close`)}
            to={linkTo}
            {...props}
          >
            <TimesIcon />
          </Link>
        )}
      </I18n>
    );
  }
  return (
    <I18n>
      {({ i18n }) => (
        <Button
          variant="plain"
          className="pf-c-card__close"
          aria-label={i18n._(t`Close`)}
          {...props}
        >
          <TimesIcon />
        </Button>
      )}
    </I18n>
  );
}
CardCloseButton.propTypes = {
  linkTo: string,
};
CardCloseButton.defaultProps = {
  linkTo: null,
};

export default CardCloseButton;
