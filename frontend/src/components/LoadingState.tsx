import React from 'react';
import { Box, CircularProgress, Typography, Skeleton } from '@mui/material';

interface LoadingStateProps {
  variant?: 'spinner' | 'skeleton';
  text?: string;
  height?: string | number;
  width?: string | number;
  skeletonCount?: number;
}

const LoadingState: React.FC<LoadingStateProps> = ({
  variant = 'spinner',
  text = 'Loading...',
  height = '60vh',
  width = '100%',
  skeletonCount = 1
}) => {
  if (variant === 'skeleton') {
    return (
      <Box sx={{ width, my: 2 }}>
        {Array.from({ length: skeletonCount }).map((_, index) => (
          <Skeleton
            key={index}
            variant="rectangular"
            height={typeof height === 'number' ? height : 100}
            sx={{ mb: 2, borderRadius: 1 }}
            animation="wave"
          />
        ))}
      </Box>
    );
  }

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        height,
        width
      }}
    >
      <CircularProgress size={40} />
      {text && (
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{ mt: 2 }}
        >
          {text}
        </Typography>
      )}
    </Box>
  );
};

export default LoadingState; 