import React, { useState, useEffect } from 'react';
import { Box, CircularProgress, Alert } from '@mui/material';
import axios from '../lib/axios';
import { APIError, formatApiError, getRetryDelay } from '../lib/errorHandling';

interface AuthenticatedImageProps {
  src: string;
  alt: string;
  style?: React.CSSProperties;
  className?: string;
}

const AuthenticatedImage: React.FC<AuthenticatedImageProps> = ({ src, alt, style, className }) => {
  const [imageData, setImageData] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<APIError | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const MAX_RETRIES = 3;

  const fetchImage = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.get(src, { responseType: 'blob' });
      const objectUrl = URL.createObjectURL(response.data);
      setImageData(objectUrl);
    } catch (err) {
      const apiError = formatApiError(err);
      console.error('Error loading image:', apiError);
      setError(apiError);

      // Handle rate limit errors with retry
      if (apiError.error_code === 'RATE-QUOTA-EXC-001' && retryCount < MAX_RETRIES) {
        const delay = getRetryDelay(apiError, retryCount);
        setTimeout(() => {
          setRetryCount(prev => prev + 1);
          fetchImage();
        }, delay);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchImage();
    return () => {
      if (imageData) {
        URL.revokeObjectURL(imageData);
      }
    };
  }, [src]);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height={200}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error.message}
        {error.details && (
          <Box component="pre" sx={{ mt: 1, fontSize: '0.8em', whiteSpace: 'pre-wrap' }}>
            {typeof error.details === 'string' ? error.details : JSON.stringify(error.details, null, 2)}
          </Box>
        )}
        {retryCount > 0 && retryCount < MAX_RETRIES && (
          <Box sx={{ mt: 1 }}>
            Retrying... Attempt {retryCount} of {MAX_RETRIES}
          </Box>
        )}
      </Alert>
    );
  }

  return <img src={imageData || ''} alt={alt} style={style} className={className} />;
};

export default AuthenticatedImage; 