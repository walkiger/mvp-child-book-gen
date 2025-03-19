import React from 'react';
import { Container, Typography, Box } from '@mui/material';
import CharacterForm from '../components/CharacterForm';

const CharacterCreate: React.FC = () => {
  return (
    <Container maxWidth="md">
      <Box sx={{ mt: 4, mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Create New Character
        </Typography>
        <CharacterForm mode="create" />
      </Box>
    </Container>
  );
};

export default CharacterCreate; 