import { useState, useEffect } from 'react'
import {
  Container,
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  CardMedia,
  CardActions,
  Button,
  CircularProgress,
  Alert,
  Paper,
} from '@mui/material'
import useAuth from '../hooks/useAuth'

interface Story {
  id: number
  title: string
  mainCharacter: string
  ageGroup: string
  tone: string
  moral: string
  pageCount: number
  coverImage?: string
  createdAt: string
}

const MyStories = () => {
  const { isAuthenticated } = useAuth()
  const [stories, setStories] = useState<Story[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string>('')

  useEffect(() => {
    const fetchStories = async () => {
      try {
        // TODO: Implement API call to fetch stories
        // const response = await fetch('/api/stories')
        // const data = await response.json()
        // setStories(data)
      } catch (err) {
        setError('Failed to load stories. Please try again.')
      } finally {
        setLoading(false)
      }
    }

    if (isAuthenticated) {
      fetchStories()
    }
  }, [isAuthenticated])

  if (!isAuthenticated) {
    return (
      <Container maxWidth="sm">
        <Box sx={{ mt: 8, textAlign: 'center' }}>
          <Typography variant="h5" gutterBottom>
            Please log in to view your stories
          </Typography>
        </Box>
      </Container>
    )
  }

  if (loading) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '60vh',
        }}
      >
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Container maxWidth="lg">
      <Box sx={{ mt: 8, mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          My Stories
        </Typography>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        {stories.length === 0 ? (
          <Paper sx={{ p: 4, textAlign: 'center' }}>
            <Typography variant="h6" gutterBottom>
              No stories yet
            </Typography>
            <Typography color="text.secondary">
              Create your first story by clicking the "Generate Story" button
            </Typography>
          </Paper>
        ) : (
          <Grid container spacing={3}>
            {stories.map((story) => (
              <Grid item xs={12} sm={6} md={4} key={story.id}>
                <Card>
                  <CardMedia
                    component="img"
                    height="200"
                    image={story.coverImage || '/placeholder-story.jpg'}
                    alt={story.title}
                  />
                  <CardContent>
                    <Typography gutterBottom variant="h5" component="div">
                      {story.title}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Main Character: {story.mainCharacter}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Age Group: {story.ageGroup}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Tone: {story.tone}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Moral: {story.moral}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Pages: {story.pageCount}
                    </Typography>
                  </CardContent>
                  <CardActions>
                    <Button size="small" color="primary">
                      Read Story
                    </Button>
                    <Button size="small" color="primary">
                      Edit
                    </Button>
                    <Button size="small" color="error">
                      Delete
                    </Button>
                  </CardActions>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}
      </Box>
    </Container>
  )
}

export default MyStories 