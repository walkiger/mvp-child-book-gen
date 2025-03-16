import React from 'react';
import { Alert, AlertTitle, Button, Box } from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import { ApiError } from '../lib/errorHandling';

interface ErrorDisplayProps {
  error: ApiError;
  onRetry?: () => void;
  fullPage?: boolean;
}

const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
  error,
  onRetry,
  fullPage = false
}) => {
  const showRetry = onRetry && error.retry;

  const content = (
    <Alert
      severity="error"
      action={
        showRetry ? (
          <Button
            color="inherit"
            size="small"
            startIcon={<RefreshIcon />}
            onClick={onRetry}
          >
            Retry
          </Button>
        ) : undefined
      }
      sx={{ width: '100%' }}
    >
      <AlertTitle>{error.code || 'Error'}</AlertTitle>
      {error.message}
      {error.details && (
        <Box component="pre" sx={{ mt: 1, fontSize: '0.8em', whiteSpace: 'pre-wrap' }}>
          {error.details}
        </Box>
      )}
    </Alert>
  );

  if (fullPage) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '60vh',
          p: 2
        }}
      >
        <Box sx={{ maxWidth: 600, width: '100%' }}>
          {content}
        </Box>
      </Box>
    );
  }

  return content;
};

export default ErrorDisplay; 