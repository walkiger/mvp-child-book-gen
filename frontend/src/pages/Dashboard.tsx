import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Container,
  Grid,
  Paper,
  Typography,
  Button,
  Box,
  Card,
  CardContent,
  CardActions,
} from '@mui/material'
import useAuth from '../hooks/useAuth'
import axios from '../lib/axios'

interface Character {
  id: number
  name: string
  traits: any
  image_path: string
}

interface Story {
  id: number
  title: string
  age_group: string
  page_count: number
  character: {
    name: string
  }
}

const Dashboard = () => {
  const navigate = useNavigate()
  const { isAuthenticated } = useAuth()
  const [characters, setCharacters] = useState<Character[]>([])
  const [stories, setStories] = useState<Story[]>([])

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login')
      return
    }

    // Fetch characters and stories
    const fetchData = async () => {
      try {
        const [charactersRes, storiesRes] = await Promise.all([
          axios.get('/api/characters/'),
          axios.get('/api/stories/')
        ])
        
        setCharacters(charactersRes.data)
        setStories(storiesRes.data)
      } catch (error) {
        console.error('Error fetching dashboard data:', error)
      }
    }

    fetchData()
  }, [isAuthenticated, navigate])

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Grid container spacing={3}>
        {/* Characters Section */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h5" component="h2">
                My Characters
              </Typography>
              <Button
                variant="contained"
                color="primary"
                onClick={() => navigate('/characters/create')}
              >
                Create Character
              </Button>
            </Box>
            <Grid container spacing={2}>
              {characters.map((character) => (
                <Grid item xs={12} sm={6} key={character.id}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6">{character.name}</Typography>
                      {character.image_path && (
                        <Box
                          component="img"
                          src={character.image_path}
                          alt={character.name}
                          sx={{ width: '100%', height: 150, objectFit: 'cover', mt: 1 }}
                        />
                      )}
                    </CardContent>
                    <CardActions>
                      <Button size="small" onClick={() => navigate(`/characters/${character.id}`)}>
                        View Details
                      </Button>
                    </CardActions>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Paper>
        </Grid>

        {/* Stories Section */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h5" component="h2">
                My Stories
              </Typography>
              <Button
                variant="contained"
                color="primary"
                onClick={() => navigate('/stories/create')}
                disabled={characters.length === 0}
              >
                Create Story
              </Button>
            </Box>
            <Grid container spacing={2}>
              {stories.map((story) => (
                <Grid item xs={12} sm={6} key={story.id}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6">{story.title}</Typography>
                      <Typography color="textSecondary">
                        Character: {story.character.name}
                      </Typography>
                      <Typography color="textSecondary">
                        Age Group: {story.age_group}
                      </Typography>
                      <Typography color="textSecondary">
                        Pages: {story.page_count}
                      </Typography>
                    </CardContent>
                    <CardActions>
                      <Button size="small" onClick={() => navigate(`/stories/${story.id}`)}>
                        View Story
                      </Button>
                    </CardActions>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  )
}

export default Dashboard 