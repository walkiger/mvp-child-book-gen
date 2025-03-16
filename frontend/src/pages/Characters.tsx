import React from 'react';
import { Typography, Box, Container, Button, Paper, Grid } from '@mui/material';
import AddIcon from '@mui/icons-material/Add';

const Characters: React.FC = () => {
  return (
    <Container>
      <Box sx={{ my: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Characters
        </Typography>
        
        <Typography variant="body1" paragraph color="text.secondary">
          Create and manage characters that will appear in your stories.
        </Typography>
        
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 3 }}>
          <Button 
            variant="contained" 
            color="primary" 
            startIcon={<AddIcon />}
          >
            Create Character
          </Button>
        </Box>
        
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Paper sx={{ p: 3, textAlign: 'center' }}>
              <Typography variant="body1">
                You haven't created any characters yet. Create your first character to get started!
              </Typography>
            </Paper>
          </Grid>
        </Grid>
      </Box>
    </Container>
  );
};

export default Characters; 