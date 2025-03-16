import React, { useState, useEffect } from 'react';
import { Container, Typography, Grid, Card, CardContent, CardActions, Button, Box } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import axios from '../lib/axios';
import LoadingState from '../components/LoadingState';
import ErrorDisplay from '../components/ErrorDisplay';
import { ApiError, formatApiError, retryOperation } from '../lib/errorHandling';

interface Story {
  id: number;
  title: string;
  created_at: string;
  status: 'draft' | 'published';
  preview_image?: string;
}

const Stories: React.FC = () => {
  const [stories, setStories] = useState<Story[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  const fetchStories = async () => {
    try {
      const response = await retryOperation(async () => {
        const res = await axios.get('/api/stories/');
        if (!res.data) {
          throw new Error('No data received from server');
        }
        return res;
      });

      setStories(response.data);
      setError(null);
    } catch (err) {
      setError(formatApiError(err));
      console.error('Error fetching stories:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStories();
  }, []);

  if (loading) {
    return <LoadingState variant="skeleton" skeletonCount={3} />;
  }

  if (error) {
    return (
      <Container maxWidth="md" sx={{ mt: 4 }}>
        <ErrorDisplay 
          error={error} 
          onRetry={fetchStories}
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
            My Stories
          </Typography>
          <Button
            variant="contained"
            color="primary"
            component={RouterLink}
            to="/story-builder"
          >
            Create New Story
          </Button>
        </Box>

        {stories.length === 0 ? (
          <Typography variant="body1" color="text.secondary" align="center">
            You haven't created any stories yet. Start by creating a new story!
          </Typography>
        ) : (
          <Grid container spacing={3}>
            {stories.map((story) => (
              <Grid item xs={12} sm={6} md={4} key={story.id}>
                <Card>
                  {story.preview_image && (
                    <Box
                      component="img"
                      src={story.preview_image}
                      alt={story.title}
                      sx={{
                        width: '100%',
                        height: 140,
                        objectFit: 'cover',
                      }}
                    />
                  )}
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      {story.title}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Created: {new Date(story.created_at).toLocaleDateString()}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Status: {story.status}
                    </Typography>
                  </CardContent>
                  <CardActions>
                    <Button
                      size="small"
                      component={RouterLink}
                      to={`/stories/${story.id}`}
                    >
                      View Story
                    </Button>
                    <Button
                      size="small"
                      component={RouterLink}
                      to={`/stories/${story.id}/edit`}
                    >
                      Edit
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

export default Stories; 