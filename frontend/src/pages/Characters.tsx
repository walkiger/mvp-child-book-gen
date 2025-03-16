import React, { useState, useEffect } from 'react';
import { Container, Typography, Grid, Card, CardContent, CardActions, Button, Box, CardMedia } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import axios from '../lib/axios';
import LoadingState from '../components/LoadingState';
import ErrorDisplay from '../components/ErrorDisplay';
import { ApiError, formatApiError, retryOperation } from '../lib/errorHandling';

interface Character {
  id: number;
  name: string;
  description: string;
  traits: string[];
  image_path?: string;
  created_at: string;
}

const Characters: React.FC = () => {
  const [characters, setCharacters] = useState<Character[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  const fetchCharacters = async () => {
    try {
      const response = await retryOperation(async () => {
        const res = await axios.get('/api/characters/');
        if (!res.data) {
          throw new Error('No data received from server');
        }
        return res;
      });

      setCharacters(response.data);
      setError(null);
    } catch (err) {
      setError(formatApiError(err));
      console.error('Error fetching characters:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCharacters();
  }, []);

  if (loading) {
    return <LoadingState variant="skeleton" skeletonCount={3} />;
  }

  if (error) {
    return (
      <Container maxWidth="md" sx={{ mt: 4 }}>
        <ErrorDisplay 
          error={error} 
          onRetry={fetchCharacters}
          fullPage
        />
      </Container>
    );
  }

  return (
    <Container maxWidth="md">
      <Box sx={{ mt: 4, mb: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
          <Typography variant="h4" component="h1">
            My Characters
          </Typography>
          <Button
            variant="contained"
            color="primary"
            component={RouterLink}
            to="/characters/create"
          >
            Create New Character
          </Button>
        </Box>

        {characters.length === 0 ? (
          <Typography variant="body1" color="text.secondary" align="center">
            You haven't created any characters yet. Start by creating a new character!
          </Typography>
        ) : (
          <Grid container spacing={3}>
            {characters.map((character) => (
              <Grid item xs={12} sm={6} md={4} key={character.id}>
                <Card>
                  {character.image_path && (
                    <CardMedia
                      component="img"
                      height="140"
                      image={character.image_path}
                      alt={character.name}
                      sx={{ objectFit: 'cover' }}
                    />
                  )}
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      {character.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" noWrap>
                      {character.description}
                    </Typography>
                    <Box sx={{ mt: 1 }}>
                      {character.traits.slice(0, 3).map((trait, index) => (
                        <Typography
                          key={index}
                          variant="body2"
                          component="span"
                          sx={{
                            bgcolor: 'action.hover',
                            px: 1,
                            py: 0.5,
                            borderRadius: 1,
                            mr: 0.5,
                            display: 'inline-block',
                            mb: 0.5,
                          }}
                        >
                          {trait}
                        </Typography>
                      ))}
                      {character.traits.length > 3 && (
                        <Typography variant="body2" component="span" color="text.secondary">
                          +{character.traits.length - 3} more
                        </Typography>
                      )}
                    </Box>
                  </CardContent>
                  <CardActions>
                    <Button
                      size="small"
                      component={RouterLink}
                      to={`/characters/${character.id}`}
                    >
                      View
                    </Button>
                    <Button
                      size="small"
                      component={RouterLink}
                      to={`/characters/${character.id}/edit`}
                    >
                      Edit
                    </Button>
                    <Button
                      size="small"
                      component={RouterLink}
                      to={`/story-builder?character=${character.id}`}
                    >
                      Create Story
                    </Button>
                  </CardActions>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}
      </Box>
    </Container>
  );
};

export default Characters; 