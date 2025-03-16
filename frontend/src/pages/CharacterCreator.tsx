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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
} from '@mui/material'
import useAuth from '../hooks/useAuth'

interface Character {
  id: number
  name: string
  age: number
  personality: string
  appearance: string
  role: string
  image?: string
  createdAt: string
}

const CharacterCreator = () => {
  const { isAuthenticated } = useAuth()
  const [characters, setCharacters] = useState<Character[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string>('')
  const [openDialog, setOpenDialog] = useState(false)
  const [newCharacter, setNewCharacter] = useState<Partial<Character>>({
    name: '',
    age: 5,
    personality: '',
    appearance: '',
    role: 'main',
  })

  useEffect(() => {
    const fetchCharacters = async () => {
      try {
        // TODO: Implement API call to fetch characters
        // const response = await fetch('/api/characters')
        // const data = await response.json()
        // setCharacters(data)
      } catch (err) {
        setError('Failed to load characters. Please try again.')
      } finally {
        setLoading(false)
      }
    }

    if (isAuthenticated) {
      fetchCharacters()
    }
  }, [isAuthenticated])

  const handleOpenDialog = () => {
    setOpenDialog(true)
  }

  const handleCloseDialog = () => {
    setOpenDialog(false)
    setNewCharacter({
      name: '',
      age: 5,
      personality: '',
      appearance: '',
      role: 'main',
    })
  }

  const handleTextChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setNewCharacter((prev) => ({ ...prev, [name as string]: value }))
  }

  const handleSelectChange = (e: SelectChangeEvent) => {
    const { name, value } = e.target
    setNewCharacter((prev) => ({ ...prev, [name as string]: value }))
  }

  const handleSubmit = async () => {
    try {
      // TODO: Implement API call to create character
      // const response = await fetch('/api/characters', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(newCharacter),
      // })
      // const data = await response.json()
      // setCharacters((prev) => [...prev, data])
      handleCloseDialog()
    } catch (err) {
      setError('Failed to create character. Please try again.')
    }
  }

  if (!isAuthenticated) {
    return (
      <Container maxWidth="sm">
        <Box sx={{ mt: 8, textAlign: 'center' }}>
          <Typography variant="h5" gutterBottom>
            Please log in to create characters
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
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            mb: 4,
          }}
        >
          <Typography variant="h4" component="h1">
            My Characters
          </Typography>
          <Button variant="contained" onClick={handleOpenDialog}>
            Create New Character
          </Button>
        </Box>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        {characters.length === 0 ? (
          <Paper sx={{ p: 4, textAlign: 'center' }}>
            <Typography variant="h6" gutterBottom>
              No characters yet
            </Typography>
            <Typography color="text.secondary">
              Create your first character by clicking the "Create New Character" button
            </Typography>
          </Paper>
        ) : (
          <Grid container spacing={3}>
            {characters.map((character) => (
              <Grid item xs={12} sm={6} md={4} key={character.id}>
                <Card>
                  <CardMedia
                    component="img"
                    height="200"
                    image={character.image || '/placeholder-character.jpg'}
                    alt={character.name}
                  />
                  <CardContent>
                    <Typography gutterBottom variant="h5" component="div">
                      {character.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Age: {character.age}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Role: {character.role}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Personality: {character.personality}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Appearance: {character.appearance}
                    </Typography>
                  </CardContent>
                  <CardActions>
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

      <Dialog open={openDialog} onClose={handleCloseDialog}>
        <DialogTitle>Create New Character</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              autoFocus
              margin="dense"
              label="Character Name"
              name="name"
              type="text"
              fullWidth
              value={newCharacter.name}
              onChange={handleTextChange}
            />
            <TextField
              margin="dense"
              label="Age"
              name="age"
              type="number"
              fullWidth
              value={newCharacter.age}
              onChange={handleTextChange}
            />
            <FormControl fullWidth>
              <InputLabel>Role</InputLabel>
              <Select
                name="role"
                value={newCharacter.role}
                label="Role"
                onChange={handleSelectChange}
              >
                <MenuItem value="main">Main Character</MenuItem>
                <MenuItem value="supporting">Supporting Character</MenuItem>
                <MenuItem value="antagonist">Antagonist</MenuItem>
              </Select>
            </FormControl>
            <TextField
              margin="dense"
              label="Personality"
              name="personality"
              type="text"
              fullWidth
              multiline
              rows={3}
              value={newCharacter.personality}
              onChange={handleTextChange}
            />
            <TextField
              margin="dense"
              label="Appearance"
              name="appearance"
              type="text"
              fullWidth
              multiline
              rows={3}
              value={newCharacter.appearance}
              onChange={handleTextChange}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained">
            Create
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  )
}

export default CharacterCreator 