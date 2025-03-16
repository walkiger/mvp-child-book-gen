import React from 'react';
import { Typography, Box, Container } from '@mui/material';

const Stories: React.FC = () => {
  return (
    <Container>
      <Box sx={{ my: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Stories
        </Typography>
        <Typography variant="body1">
          Browse and manage your stories. Create new adventures for your characters.
        </Typography>
      </Box>
    </Container>
  );
};

export default Stories; 