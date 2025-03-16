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
  Paper,
} from '@mui/material'
import useAuth from '../hooks/useAuth'
import LoadingState from '../components/LoadingState'
import ErrorDisplay from '../components/ErrorDisplay'
import { ApiError, formatApiError, retryOperation } from '../lib/errorHandling'

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
  const [error, setError] = useState<ApiError | null>(null)

  const fetchStories = async () => {
    try {
      const response = await fetch('/api/stories')
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      setStories(data)
      setError(null)
    } catch (err) {
      const apiError = formatApiError(err)
      setError(apiError)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
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
    return <LoadingState variant="spinner" text="Loading stories..." />
  }

  return (
    <Container maxWidth="lg">
      <Box sx={{ mt: 8, mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          My Stories
        </Typography>
        {error && (
          <ErrorDisplay 
            error={error} 
            onRetry={error.retry ? fetchStories : undefined}
          />
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