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
  CircularProgress,
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
  const [error, setError] = useState<string>('')
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
      const response = await axios.get('/api/characters/')
      setCharacters(response.data)
    } catch (err) {
      setError('Failed to load characters. Please try again.')
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
      setError('Please select a character')
      return
    }
    
    setLoading(true)
    setError('')

    try {
      // Format parameters for API
      const apiParams = {
        title: storyParams.title,
        age_group: storyParams.ageGroup,
        story_tone: storyParams.tone,
        moral_lesson: storyParams.moral,
        page_count: storyParams.pageCount,
        character_id: storyParams.character_id
      }
      
      // Call story generation API
      const response = await axios.post('/api/stories/', apiParams)
      
      // Redirect to the newly created story
      navigate(`/stories/${response.data.id}`)
    } catch (err) {
      console.error('Error generating story:', err)
      setError('Failed to generate story. Please try again.')
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
            <Alert severity="error" sx={{ width: '100%', mb: 2 }}>
              {error}
            </Alert>
          )}
          
          <Box sx={{ width: '100%', mb: 4 }}>
            <Typography variant="h6" gutterBottom>
              1. Select a Character
            </Typography>
            {loadingCharacters ? (
              <Box display="flex" justifyContent="center" mt={2}>
                <CircularProgress />
              </Box>
            ) : characters.length === 0 ? (
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
                  >
                    {characters.map((character) => (
                      <MenuItem key={character.id} value={character.id.toString()}>
                        {character.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                
                {selectedCharacter && (
                  <Card sx={{ mt: 2, display: 'flex', flexDirection: 'row', alignItems: 'center' }}>
                    {selectedCharacter.image_path && (
                      <CardMedia
                        component="img"
                        sx={{ width: 120, height: 120, objectFit: 'contain' }}
                        image={selectedCharacter.image_path}
                        alt={selectedCharacter.name}
                      />
                    )}
                    <Box sx={{ p: 2 }}>
                      <Typography variant="h6">{selectedCharacter.name}</Typography>
                      <Box display="flex" flexWrap="wrap" gap={0.5} mt={1}>
                        {selectedCharacter.traits.map((trait) => (
                          <Typography key={trait} variant="body2" sx={{ bgcolor: 'grey.100', px: 1, py: 0.5, borderRadius: 1 }}>
                            {trait}
                          </Typography>
                        ))}
                      </Box>
                    </Box>
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
              margin="normal"
              required
              fullWidth
              id="title"
              label="Story Title"
              name="title"
              value={storyParams.title}
              onChange={handleChange}
            />
            
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth margin="normal">
                  <InputLabel id="age-group-label">Age Group</InputLabel>
                  <Select
                    labelId="age-group-label"
                    id="ageGroup"
                    name="ageGroup"
                    value={storyParams.ageGroup}
                    label="Age Group"
                    onChange={handleChange}
                  >
                    <MenuItem value="1-2">1-2 years</MenuItem>
                    <MenuItem value="3-6">3-6 years</MenuItem>
                    <MenuItem value="6-9">6-9 years</MenuItem>
                    <MenuItem value="10-12">10-12 years</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <FormControl fullWidth margin="normal">
                  <InputLabel id="tone-label">Story Tone</InputLabel>
                  <Select
                    labelId="tone-label"
                    id="tone"
                    name="tone"
                    value={storyParams.tone}
                    label="Story Tone"
                    onChange={handleChange}
                  >
                    <MenuItem value="whimsical">Whimsical</MenuItem>
                    <MenuItem value="educational">Educational</MenuItem>
                    <MenuItem value="adventurous">Adventurous</MenuItem>
                    <MenuItem value="calming">Calming</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
            
            <FormControl fullWidth margin="normal">
              <InputLabel id="moral-label">Moral Lesson</InputLabel>
              <Select
                labelId="moral-label"
                id="moral"
                name="moral"
                value={storyParams.moral}
                label="Moral Lesson"
                onChange={handleChange}
              >
                <MenuItem value="kindness">Kindness</MenuItem>
                <MenuItem value="courage">Courage</MenuItem>
                <MenuItem value="friendship">Friendship</MenuItem>
                <MenuItem value="honesty">Honesty</MenuItem>
                <MenuItem value="perseverance">Perseverance</MenuItem>
              </Select>
            </FormControl>
            
            <Box sx={{ mt: 2, mb: 2 }}>
              <Typography gutterBottom>Number of Pages</Typography>
              <Slider
                value={storyParams.pageCount}
                onChange={handleSliderChange}
                min={3}
                max={10}
                marks
                valueLabelDisplay="auto"
              />
            </Box>
            
            <Button
              type="submit"
              fullWidth
              variant="contained"
              disabled={loading || !selectedCharacter}
              sx={{ mt: 3, mb: 2 }}
            >
              {loading ? <CircularProgress size={24} /> : 'Generate Story'}
            </Button>
          </Box>
        </Paper>
      </Box>
    </Container>
  )
}

export default StoryGenerator 