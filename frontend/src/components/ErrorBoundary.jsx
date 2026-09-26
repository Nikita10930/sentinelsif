import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('[SentinelSIF Error Boundary Caught Error]:', error, errorInfo);
    this.setState({ errorInfo });
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary-card">
          <div className="error-boundary-header">
            <span className="error-icon">⚠️</span>
            <h4>Component Telemetry Failure</h4>
          </div>
          <p className="error-boundary-msg">
            {this.props.fallbackMessage ||
              'A critical rendering exception occurred in this operational panel.'}
          </p>
          <div className="error-boundary-details">
            <code>{this.state.error?.message || 'Unknown runtime error'}</code>
          </div>
          <button className="btn-secondary" onClick={this.handleReset}>
            Reinitialize Component
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
