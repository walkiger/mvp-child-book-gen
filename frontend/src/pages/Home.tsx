import React from 'react';
import { Typography, Box, Container, Button, Grid, Paper } from '@mui/material';
import { Link } from 'react-router-dom';
import BookIcon from '@mui/icons-material/Book';
import PeopleIcon from '@mui/icons-material/People';

const Home: React.FC = () => {
  return (
    <Container>
      <Box sx={{ my: 4 }}>
        <Typography variant="h3" component="h1" gutterBottom align="center">
          Child Book Generator
        </Typography>
        
        <Typography variant="h6" paragraph align="center" color="text.secondary" sx={{ mb: 4 }}>
          Create personalized stories for children with custom characters and adventures
        </Typography>

        <Grid container spacing={4} justifyContent="center">
          <Grid item xs={12} sm={6} md={4}>
            <Paper sx={{ p: 3, height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
              <PeopleIcon sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
              <Typography variant="h5" component="h2" gutterBottom align="center">
                Characters
              </Typography>
              <Typography align="center" paragraph>
                Create and customize characters for your stories
              </Typography>
              <Button 
                component={Link} 
                to="/characters" 
                variant="contained" 
                color="primary"
                sx={{ mt: 'auto' }}
              >
                Manage Characters
              </Button>
            </Paper>
          </Grid>
          
          <Grid item xs={12} sm={6} md={4}>
            <Paper sx={{ p: 3, height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
              <BookIcon sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
              <Typography variant="h5" component="h2" gutterBottom align="center">
                Stories
              </Typography>
              <Typography align="center" paragraph>
                Generate beautiful, illustrated stories for children
              </Typography>
              <Button 
                component={Link} 
                to="/story-builder" 
                variant="contained" 
                color="primary"
                sx={{ mt: 'auto' }}
              >
                Create Stories
              </Button>
            </Paper>
          </Grid>
        </Grid>
      </Box>
    </Container>
  );
};

export default Home; 