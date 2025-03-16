import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Box, Typography, Button, Container, Paper } from '@mui/material';
import ErrorDisplay from './ErrorDisplay';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
    };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
  }

  private handleRetry = () => {
    this.setState({ hasError: false, error: null });
    window.location.reload();
  };

  public render() {
    if (this.state.hasError) {
      return (
        <Container maxWidth="sm">
          <Box
            sx={{
              minHeight: '100vh',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Paper
              elevation={3}
              sx={{
                p: 4,
                width: '100%',
                textAlign: 'center',
              }}
            >
              <Typography variant="h4" gutterBottom>
                Oops! Something went wrong
              </Typography>

              {this.state.error && (
                <ErrorDisplay
                  error={{
                    message: this.state.error.message,
                    code: 'APP_ERROR',
                    retry: true,
                    details: 'An unexpected error occurred in the application.',
                  }}
                  onRetry={this.handleRetry}
                />
              )}

              <Box sx={{ mt: 4 }}>
                <Button
                  variant="contained"
                  onClick={this.handleRetry}
                  size="large"
                >
                  Retry
                </Button>
              </Box>
            </Paper>
          </Box>
        </Container>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary; 