import React from 'react';
import { Typography, Box, Container, Button, Paper } from '@mui/material';
import CreateIcon from '@mui/icons-material/Create';

const StoryBuilder: React.FC = () => {
  return (
    <Container>
      <Box sx={{ my: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Story Builder
        </Typography>
        
        <Typography variant="body1" paragraph>
          Create magical stories for children with your custom characters.
        </Typography>
        
        <Paper sx={{ p: 3, mt: 3 }}>
          <Typography variant="h6" gutterBottom>
            Start a New Story
          </Typography>
          
          <Typography variant="body2" paragraph>
            Select your characters, set the theme, and let the magic begin!
          </Typography>
          
          <Button 
            variant="contained" 
            color="primary" 
            startIcon={<CreateIcon />}
            sx={{ mt: 2 }}
          >
            Create New Story
          </Button>
        </Paper>
      </Box>
    </Container>
  );
};

export default StoryBuilder; 