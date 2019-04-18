import React, { Component } from 'react';

const RootDialogContext = React.createContext({});

export class RootDialogProvider extends Component {
  constructor (props) {
    super(props);

    this.state = {
      value: {
        title: null,
        setRootDialogMessage: ({ title, bodyText, variant }) => {
          const { value } = this.state;
          this.setState({ value: { ...value, title, bodyText, variant } });
        },
        clearRootDialogMessage: () => {
          const { value } = this.state;
          this.setState({ value: { ...value, title: null, bodyText: null, variant: null } });
        },
        ...props.value,
      }
    };
  }

  render () {
    const {
      children
    } = this.props;

    const {
      value
    } = this.state;

    return (
      <RootDialogContext.Provider value={value}>
        {children}
      </RootDialogContext.Provider>
    );
  }
}

export const RootDialog = ({ children }) => (
  <RootDialogContext.Consumer>
    {value => children(value)}
  </RootDialogContext.Consumer>
);

export function withRootDialog (Child) {
  return (props) => (
    <RootDialogContext.Consumer>
      {context => <Child {...props} {...context} />}
    </RootDialogContext.Consumer>
  );
}
