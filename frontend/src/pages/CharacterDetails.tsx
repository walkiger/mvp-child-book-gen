import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Container,
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  CardMedia,
  Button,
  CircularProgress,
  Alert,
  Chip,
} from '@mui/material'
import EditIcon from '@mui/icons-material/Edit'
import DeleteIcon from '@mui/icons-material/Delete'
import BookIcon from '@mui/icons-material/Book'
import axios from '../lib/axios'
import AuthenticatedImage from '../components/AuthenticatedImage'

interface Character {
  id: number
  name: string
  traits: string[]
  image_path?: string
  generated_images?: string[]
}

const CharacterDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [character, setCharacter] = useState<Character | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchCharacter()
  }, [id])

  const fetchCharacter = async () => {
    try {
      console.log(`Fetching character with ID ${id} from API`)
      const response = await axios.get(`/api/characters/${id}`)
      console.log('Character data received:', response.data)
      setCharacter(response.data)
    } catch (err) {
      console.error('Error fetching character:', err)
      setError('Failed to fetch character details')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async () => {
    if (!window.confirm('Are you sure you want to delete this character?')) {
      return
    }

    try {
      await axios.delete(`/api/characters/${id}`)
      navigate('/characters')
    } catch (err) {
      console.error('Error deleting character:', err)
      setError('Failed to delete character')
    }
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    )
  }

  if (error) {
    return (
      <Container>
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      </Container>
    )
  }

  if (!character) {
    return (
      <Container>
        <Alert severity="error" sx={{ mt: 2 }}>
          Character not found
        </Alert>
      </Container>
    )
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Typography variant="h4" component="h1">
          {character.name}
        </Typography>
        <Box>
          <Button
            variant="contained"
            startIcon={<BookIcon />}
            onClick={() => navigate(`/stories?character=${character.id}`)}
            sx={{ mr: 1 }}
          >
            Use in Story
          </Button>
          <Button
            variant="contained"
            startIcon={<EditIcon />}
            onClick={() => navigate(`/characters/${id}/edit`)}
            sx={{ mr: 1 }}
          >
            Edit
          </Button>
          <Button
            variant="outlined"
            color="error"
            startIcon={<DeleteIcon />}
            onClick={handleDelete}
          >
            Delete
          </Button>
        </Box>
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Traits
              </Typography>
              <Box display="flex" flexWrap="wrap" gap={1}>
                {character.traits.map((trait) => (
                  <Chip key={trait} label={trait} />
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          {character.image_path && (
            <Card>
              <AuthenticatedImage
                src={character.image_path}
                alt={character.name}
                style={{ height: '300px', width: '100%', objectFit: 'cover' }}
              />
            </Card>
          )}
        </Grid>

        {character.generated_images && character.generated_images.length > 0 && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Generated Images
                </Typography>
                <Grid container spacing={2}>
                  {character.generated_images.map((image, index) => (
                    <Grid item xs={12} sm={6} md={3} key={index}>
                      <Card>
                        <AuthenticatedImage
                          src={image}
                          alt={`${character.name} - Option ${index + 1}`}
                          style={{ height: '200px', width: '100%', objectFit: 'cover' }}
                        />
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>
    </Container>
  )
}

export default CharacterDetails 