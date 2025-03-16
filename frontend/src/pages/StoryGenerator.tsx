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
import { ApiError, formatApiError, retryOperation } from '../lib/errorHandling'

interface Character {
  id: number
  name: string
  traits: string[]
  image_path?: string
}

interface StoryParams {
  title: string
  ageGroup: string
  tone: string
  moral: string
  pageCount: number
  character_id: number
}

const StoryGenerator = () => {
  const { isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [loading, setLoading] = useState(false)
  const [loadingCharacters, setLoadingCharacters] = useState(true)
  const [error, setError] = useState<ApiError | null>(null)
  const [characters, setCharacters] = useState<Character[]>([])
  const [selectedCharacter, setSelectedCharacter] = useState<Character | null>(null)
  const [storyParams, setStoryParams] = useState<StoryParams>({
    title: '',
    ageGroup: '3-6',
    tone: 'whimsical',
    moral: 'kindness',
    pageCount: 5,
    character_id: 0,
  })

  // Parse URL query parameters
  useEffect(() => {
    if (isAuthenticated) {
      const searchParams = new URLSearchParams(location.search);
      const characterId = searchParams.get('character');
      
      if (characterId) {
        // Pre-select character if ID is in the URL
        const id = parseInt(characterId);
        if (!isNaN(id)) {
          setStoryParams(prev => ({
            ...prev,
            character_id: id
          }));
        }
      }
    }
  }, [isAuthenticated, location.search]);

  // Fetch characters when component mounts
  useEffect(() => {
    if (isAuthenticated) {
      fetchCharacters()
    }
  }, [isAuthenticated])

  // Set selected character when characters are loaded or character_id changes
  useEffect(() => {
    if (characters.length > 0 && storyParams.character_id) {
      const character = characters.find(c => c.id === storyParams.character_id) || null;
      setSelectedCharacter(character);
    }
  }, [characters, storyParams.character_id]);

  const fetchCharacters = async () => {
    setLoadingCharacters(true)
    try {
      const response = await retryOperation(async () => {
        const res = await axios.get('/api/characters/')
        if (!res.data) {
          throw new Error('No data received from server')
        }
        return res
      })
      setCharacters(response.data)
      setError(null)
    } catch (err) {
      const apiError = formatApiError(err)
      setError(apiError)
      console.error('Error fetching characters:', err)
    } finally {
      setLoadingCharacters(false)
    }
  }

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement> | SelectChangeEvent
  ) => {
    const { name, value } = e.target
    setStoryParams((prev) => ({ ...prev, [name as string]: value }))
  }

  const handleCharacterSelect = (e: SelectChangeEvent) => {
    const characterId = parseInt(e.target.value)
    const character = characters.find(c => c.id === characterId) || null
    setSelectedCharacter(character)
    setStoryParams((prev) => ({ ...prev, character_id: characterId }))
  }

  const handleSliderChange = (_event: Event, newValue: number | number[]) => {
    setStoryParams((prev) => ({ ...prev, pageCount: newValue as number }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedCharacter) {
      setError({
        message: 'Please select a character',
        code: 'VALIDATION_ERROR',
        retry: false,
        details: 'A character is required to generate a story.'
      })
      return
    }

    if (!storyParams.title.trim()) {
      setError({
        message: 'Please enter a story title',
        code: 'VALIDATION_ERROR',
        retry: false,
        details: 'A title is required for your story.'
      })
      return
    }
    
    setLoading(true)
    setError(null)

    try {
      await retryOperation(async () => {
        // Format parameters for API
        const apiParams = {
          title: storyParams.title.trim(),
          age_group: storyParams.ageGroup,
          story_tone: storyParams.tone,
          moral_lesson: storyParams.moral,
          page_count: storyParams.pageCount,
          character_id: storyParams.character_id
        }
        
        // Call story generation API
        const response = await axios.post('/api/stories/', apiParams)
        if (!response.data || !response.data.id) {
          throw new Error('Invalid response from server')
        }
        
        // Redirect to the newly created story
        navigate(`/stories/${response.data.id}`)
      })
    } catch (err) {
      const apiError = formatApiError(err)
      setError(apiError)
      console.error('Error generating story:', err)
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
    return <LoadingState variant="spinner" text="Loading characters..." />
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
            <ErrorDisplay 
              error={error} 
              onRetry={error.retry ? fetchCharacters : undefined}
            />
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
                    value={storyParams.character_id.toString()}
                    label="Character"
                    onChange={handleCharacterSelect}
                    error={Boolean(error?.code === 'VALIDATION_ERROR' && !selectedCharacter)}
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
            
            <TextField
              fullWidth
              margin="normal"
              label="Story Title"
              name="title"
              value={storyParams.title}
              onChange={handleChange}
              error={Boolean(error?.code === 'VALIDATION_ERROR' && !storyParams.title.trim())}
              helperText={error?.code === 'VALIDATION_ERROR' && !storyParams.title.trim() ? 'Title is required' : ''}
              disabled={loading}
            />
            
            <FormControl fullWidth margin="normal">
              <InputLabel>Age Group</InputLabel>
              <Select
                name="ageGroup"
                value={storyParams.ageGroup}
                label="Age Group"
                onChange={handleChange}
                disabled={loading}
              >
                <MenuItem value="3-6">3-6 years</MenuItem>
                <MenuItem value="7-9">7-9 years</MenuItem>
                <MenuItem value="10-12">10-12 years</MenuItem>
              </Select>
            </FormControl>
            
            <FormControl fullWidth margin="normal">
              <InputLabel>Story Tone</InputLabel>
              <Select
                name="tone"
                value={storyParams.tone}
                label="Story Tone"
                onChange={handleChange}
                disabled={loading}
              >
                <MenuItem value="whimsical">Whimsical</MenuItem>
                <MenuItem value="educational">Educational</MenuItem>
                <MenuItem value="adventurous">Adventurous</MenuItem>
                <MenuItem value="funny">Funny</MenuItem>
              </Select>
            </FormControl>
            
            <FormControl fullWidth margin="normal">
              <InputLabel>Moral Lesson</InputLabel>
              <Select
                name="moral"
                value={storyParams.moral}
                label="Moral Lesson"
                onChange={handleChange}
                disabled={loading}
              >
                <MenuItem value="kindness">Kindness</MenuItem>
                <MenuItem value="honesty">Honesty</MenuItem>
                <MenuItem value="perseverance">Perseverance</MenuItem>
                <MenuItem value="friendship">Friendship</MenuItem>
                <MenuItem value="responsibility">Responsibility</MenuItem>
              </Select>
            </FormControl>
            
            <Box sx={{ mt: 3 }}>
              <Typography gutterBottom>Number of Pages: {storyParams.pageCount}</Typography>
              <Slider
                value={storyParams.pageCount}
                onChange={handleSliderChange}
                min={5}
                max={20}
                step={1}
                marks
                valueLabelDisplay="auto"
                disabled={loading}
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