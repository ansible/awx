import React from 'react';

class CapitalizeText extends React.Component {
  upperCaseFirstLetter = (string) => (typeof string === 'string' ? string.charAt(0).toUpperCase() + string.slice(1) : '');

  render () {
    const { text } = this.props;
    return (
      this.upperCaseFirstLetter(text)
    );
  }
}

export default CapitalizeText;
