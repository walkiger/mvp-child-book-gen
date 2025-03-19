import { useState, useEffect } from 'react'
import {
  Container,
  Box,
  Typography,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Slider,
  Paper,
  Alert,
  SelectChangeEvent,
  Card,
  CardMedia,
  Grid,
  Divider,
} from '@mui/material'
import { useNavigate, useLocation } from 'react-router-dom'
import useAuth from '../hooks/useAuth'
import axios from '../lib/axios'
import LoadingState from '../components/LoadingState'
import ErrorDisplay from '../components/ErrorDisplay'
import { APIError, formatApiError, isRetryableError } from '../lib/errorHandling'
import AuthenticatedImage from '../components/AuthenticatedImage'

interface Character {
  id: number
  name: string
  traits: string[]
  image_path?: string
}

interface StoryParams {
  character_id: string
  age_group: string
  tone: string
  moral: string
  page_count: number
}

const StoryGenerator = () => {
  const { isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [loading, setLoading] = useState(false)
  const [loadingCharacters, setLoadingCharacters] = useState(true)
  const [error, setError] = useState<APIError | null>(null)
  const [characters, setCharacters] = useState<Character[]>([])
  const [selectedCharacter, setSelectedCharacter] = useState<Character | null>(null)
  const [storyParams, setStoryParams] = useState<StoryParams>({
    character_id: '',
    age_group: '5-8',
    tone: 'fun',
    moral: '',
    page_count: 10
  })

  useEffect(() => {
    fetchCharacters()
  }, [])

  const fetchCharacters = async () => {
    try {
      const response = await axios.get('/api/characters')
      setCharacters(response.data)
      
      // If character ID was passed in location state, select it
      if (location.state?.characterId) {
        const character = response.data.find(
          (c: Character) => c.id === location.state.characterId
        )
        if (character) {
          setSelectedCharacter(character)
          setStoryParams(prev => ({
            ...prev,
            character_id: character.id.toString()
          }))
        }
      }
    } catch (err) {
      setError(formatApiError(err))
    } finally {
      setLoadingCharacters(false)
    }
  }

  const handleCharacterSelect = (event: SelectChangeEvent) => {
    const characterId = event.target.value
    const character = characters.find(c => c.id.toString() === characterId)
    setSelectedCharacter(character || null)
    setStoryParams(prev => ({
      ...prev,
      character_id: characterId
    }))
  }

  const handleSubmit = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await axios.post('/api/stories/generate', storyParams)
      navigate(`/stories/${response.data.id}`)
    } catch (err) {
      setError(formatApiError(err))
    } finally {
      setLoading(false)
    }
  }

  if (!isAuthenticated) {
    return (
      <Container maxWidth="sm">
        <Box sx={{ mt: 8, textAlign: 'center' }}>
          <Typography variant="h5" gutterBottom>
            Please log in to generate stories
          </Typography>
        </Box>
      </Container>
    )
  }

  if (loadingCharacters) {
    return <LoadingState />
  }

  return (
    <Container maxWidth="md">
      <Box
        sx={{
          mt: 8,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        <Paper
          elevation={3}
          sx={{
            p: 4,
            width: '100%',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
          }}
        >
          <Typography component="h1" variant="h4" gutterBottom>
            Generate Your Story
          </Typography>
          
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error.message}
              {error.details && (
                <Typography variant="body2" sx={{ mt: 1 }}>
                  {typeof error.details === 'string' ? error.details : JSON.stringify(error.details)}
                </Typography>
              )}
            </Alert>
          )}
          
          <Box sx={{ width: '100%', mb: 4 }}>
            <Typography variant="h6" gutterBottom>
              1. Select a Character
            </Typography>
            {characters.length === 0 ? (
              <Alert severity="info" sx={{ mb: 2 }}>
                You don't have any characters yet. <Button onClick={() => navigate('/characters/create')}>Create a character</Button> first.
              </Alert>
            ) : (
              <>
                <FormControl fullWidth margin="normal">
                  <InputLabel id="character-select-label">Character</InputLabel>
                  <Select
                    labelId="character-select-label"
                    id="character"
                    value={storyParams.character_id}
                    label="Character"
                    onChange={handleCharacterSelect}
                    error={Boolean(error?.error_code === 'VALIDATION_ERROR' && !selectedCharacter)}
                  >
                    {characters.map((character) => (
                      <MenuItem key={character.id} value={character.id.toString()}>
                        {character.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                
                {selectedCharacter && (
                  <Card sx={{ mt: 2, mb: 4 }}>
                    <Grid container>
                      {selectedCharacter.image_path && (
                        <Grid item xs={12} sm={4}>
                          <CardMedia
                            component="img"
                            height="200"
                            image={selectedCharacter.image_path}
                            alt={selectedCharacter.name}
                            sx={{ objectFit: 'contain' }}
                          />
                        </Grid>
                      )}
                      <Grid item xs={12} sm={selectedCharacter.image_path ? 8 : 12}>
                        <Box sx={{ p: 2 }}>
                          <Typography variant="h6">{selectedCharacter.name}</Typography>
                          <Typography variant="body2" color="text.secondary">
                            Traits: {selectedCharacter.traits.join(', ')}
                          </Typography>
                        </Box>
                      </Grid>
                    </Grid>
                  </Card>
                )}
              </>
            )}
          </Box>
          
          <Divider sx={{ width: '100%', my: 2 }} />
          
          <Box component="form" onSubmit={handleSubmit} sx={{ width: '100%' }}>
            <Typography variant="h6" gutterBottom>
              2. Story Details
            </Typography>
            
            <FormControl fullWidth margin="normal">
              <InputLabel id="age-group-label">Age Group</InputLabel>
              <Select
                labelId="age-group-label"
                id="age_group"
                value={storyParams.age_group}
                label="Age Group"
                onChange={(e) => setStoryParams(prev => ({ ...prev, age_group: e.target.value }))}
                error={Boolean(error?.error_code === 'VALIDATION_ERROR' && !storyParams.age_group)}
              >
                <MenuItem value="3-5">3-5 years</MenuItem>
                <MenuItem value="5-8">5-8 years</MenuItem>
                <MenuItem value="8-12">8-12 years</MenuItem>
              </Select>
            </FormControl>
            
            <FormControl fullWidth margin="normal">
              <InputLabel id="tone-label">Story Tone</InputLabel>
              <Select
                labelId="tone-label"
                id="tone"
                value={storyParams.tone}
                label="Story Tone"
                onChange={(e) => setStoryParams(prev => ({ ...prev, tone: e.target.value }))}
                error={Boolean(error?.error_code === 'VALIDATION_ERROR' && !storyParams.tone)}
              >
                <MenuItem value="fun">Fun & Playful</MenuItem>
                <MenuItem value="educational">Educational</MenuItem>
                <MenuItem value="adventurous">Adventurous</MenuItem>
                <MenuItem value="mysterious">Mysterious</MenuItem>
              </Select>
            </FormControl>
            
            <TextField
              fullWidth
              margin="normal"
              label="Moral of the Story"
              value={storyParams.moral}
              onChange={(e) => setStoryParams(prev => ({ ...prev, moral: e.target.value }))}
              error={Boolean(error?.error_code === 'VALIDATION_ERROR' && !storyParams.moral)}
              helperText="What lesson should the story teach?"
            />
            
            <Box sx={{ mt: 3 }}>
              <Typography gutterBottom>
                Number of Pages: {storyParams.page_count}
              </Typography>
              <Slider
                value={storyParams.page_count}
                onChange={(_, value) => setStoryParams(prev => ({ ...prev, page_count: value as number }))}
                min={5}
                max={20}
                step={1}
                marks
                valueLabelDisplay="auto"
              />
            </Box>
            
            <Box sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
              <Button
                type="submit"
                variant="contained"
                size="large"
                disabled={loading || !selectedCharacter}
                sx={{ minWidth: 200 }}
              >
                {loading ? (
                  <LoadingState variant="spinner" text="Generating Story..." height={24} />
                ) : (
                  'Generate Story'
                )}
              </Button>
            </Box>
          </Box>
        </Paper>
      </Box>
    </Container>
  )
}

export default StoryGenerator 