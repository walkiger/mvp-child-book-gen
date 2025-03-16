import React, { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  Container,
  Typography,
  TextField,
  Button,
  Box,
  CircularProgress,
  Grid,
  Chip,
  Card,
  CardMedia,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  SelectChangeEvent,
  IconButton,
  Tooltip,
  AlertTitle
} from '@mui/material'
import { AxiosError } from 'axios'
import axios from '../lib/axios'
import EditIcon from '@mui/icons-material/Edit'
import CheckIcon from '@mui/icons-material/Check'
import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh'

interface CharacterFormData {
  name: string
  traits: string[]
  imagePrompt?: string
  imagePath?: string
}

interface ImageGenerationData {
  prompt: string
  dalleVersion: 'dall-e-2' | 'dall-e-3'
  isLoading: boolean
  regenerationCount?: number
}

interface RateLimitInfo {
  requests: number
  tokens: number
  resetIn: number
}

interface CharacterFormProps {
  mode: 'create' | 'edit'
}

const CharacterForm: React.FC<CharacterFormProps> = ({ mode }) => {
  const navigate = useNavigate()
  const { id } = useParams<{ id: string }>()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [formData, setFormData] = useState<CharacterFormData>({
    name: '',
    traits: [],
  })
  const [newTrait, setNewTrait] = useState('')
  const [generatedImages, setGeneratedImages] = useState<string[]>([])
  const [showImageDialog, setShowImageDialog] = useState(false)
  const [rateLimitError, setRateLimitError] = useState(false)
  const [characterId, setCharacterId] = useState<string | null>(null)
  const [step, setStep] = useState<'prompt' | 'prompt-edit' | 'images'>('prompt')
  const [rateLimitInfo, setRateLimitInfo] = useState<RateLimitInfo | null>(null)
  const [generatedSlots, setGeneratedSlots] = useState<boolean[]>([false, false, false, false])
  const [imageGenData, setImageGenData] = useState<ImageGenerationData[]>([
    { prompt: '', dalleVersion: 'dall-e-3', isLoading: false },
    { prompt: '', dalleVersion: 'dall-e-3', isLoading: false },
    { prompt: '', dalleVersion: 'dall-e-3', isLoading: false },
    { prompt: '', dalleVersion: 'dall-e-3', isLoading: false }
  ])
  const [isEditingPrompt, setIsEditingPrompt] = useState(false)
  const [editedPrompt, setEditedPrompt] = useState('')
  const [isEnhancingPrompt, setIsEnhancingPrompt] = useState(false)
  const [enhancedPrompt, setEnhancedPrompt] = useState('')

  useEffect(() => {
    if (mode === 'edit' && id) {
      fetchCharacter()
    }
  }, [mode, id])

  // Add effect to sync with global rate limit info
  useEffect(() => {
    // Check for global rate limit info
    const checkRateLimit = () => {
      if (window.rateLimitInfo) {
        const { requests, tokens, resetIn, timestamp } = window.rateLimitInfo
        
        // Calculate how much time has passed since the rate limit was set
        const now = Date.now()
        const elapsedSeconds = Math.floor((now - timestamp) / 1000)
        
        // Adjust resetIn based on elapsed time
        const adjustedResetIn = Math.max(0, resetIn - elapsedSeconds)
        
        setRateLimitInfo({
          requests,
          tokens,
          resetIn: adjustedResetIn
        })
        
        setRateLimitError(requests <= 0 || tokens <= 0)
      }
    }
    
    // Check immediately
    checkRateLimit()
    
    // Set up periodic check
    const intervalId = setInterval(checkRateLimit, 1000)
    
    return () => clearInterval(intervalId)
  }, [])

  const fetchCharacter = async () => {
    setLoading(true)
    try {
      const response = await axios.get(`/api/characters/${id}/`)
      setFormData({
        name: response.data.name,
        traits: response.data.traits,
        imagePrompt: response.data.image_prompt,
        imagePath: response.data.image_path,
      })
      if (response.data.generated_images) {
        setGeneratedImages(response.data.generated_images)
      }
    } catch (err) {
      setError('Failed to fetch character')
      console.error('Error fetching character:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleTextChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleDalleVersionChange = (index: number, value: string) => {
    const newImageGenData = [...imageGenData]
    newImageGenData[index].dalleVersion = value as 'dall-e-2' | 'dall-e-3'
    setImageGenData(newImageGenData)
  }

  const handlePromptChange = (index: number, value: string) => {
    const newImageGenData = [...imageGenData]
    newImageGenData[index].prompt = value
    setImageGenData(newImageGenData)
  }

  const handleAddTrait = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && newTrait.trim()) {
      e.preventDefault()
      addTraits(newTrait.trim())
      setNewTrait('')
    }
  }

  const addTraits = (traitText: string) => {
    // Split by commas or multiple spaces, preserve single spaces within traits
    const traits = traitText
      .split(/,|\s{2,}/)                    // Split by commas or 2+ spaces
      .map(trait => trait.trim())           // Trim each trait
      .filter(trait => trait.length > 0)    // Remove empty traits
      .filter(trait => !formData.traits.includes(trait)); // Remove duplicates
    
    if (traits.length > 0) {
      setFormData(prev => ({
        ...prev,
        traits: [...prev.traits, ...traits]
      }));
    }
  }

  const handleAddTraitClick = () => {
    if (newTrait.trim()) {
      addTraits(newTrait.trim())
      setNewTrait('')
    }
  }

  const handleRemoveTrait = (traitToRemove: string) => {
    setFormData(prev => ({
      ...prev,
      traits: prev.traits.filter(trait => trait !== traitToRemove)
    }))
  }

  const canGenerateImage = () => {
    if (!rateLimitInfo) return true
    return rateLimitInfo.requests > 0 && rateLimitInfo.tokens > 0
  }

  const handleGenerateImage = async (index: number) => {
    if (!canGenerateImage()) {
      setRateLimitError(true)
      return
    }

    // Mark slot as loading
    const newImageGenData = [...imageGenData]
    newImageGenData[index].isLoading = true
    setImageGenData(newImageGenData)

    setLoading(true)
    try {
      const response = await axios.post(`/api/characters/${characterId}/generate-image`, {
        index,
        dalle_version: imageGenData[index].dalleVersion,
        prompt: imageGenData[index].prompt || formData.imagePrompt
      })
      
      // The response now includes a URL to our backend endpoint
      const newImages = [...generatedImages]
      newImages[index] = response.data.image_url
      setGeneratedImages(newImages)
      
      const newGeneratedSlots = [...generatedSlots]
      newGeneratedSlots[index] = true
      setGeneratedSlots(newGeneratedSlots)

      // Update image generation data with regeneration count and prompt
      const updatedImageGenData = [...imageGenData]
      updatedImageGenData[index].regenerationCount = response.data.regeneration_count || 0
      if (response.data.prompt) {
        updatedImageGenData[index].prompt = response.data.prompt
      }
      setImageGenData(updatedImageGenData)

      // Update rate limit info if provided
      if (response.data.rate_limit_info) {
        setRateLimitInfo(response.data.rate_limit_info)
      }
    } catch (err) {
      if (err instanceof AxiosError && err.response?.status === 429) {
        setRateLimitError(true)
      } else if (err instanceof AxiosError && err.response?.status === 403) {
        // Regeneration limit reached
        setError('Each image can only be regenerated once.')
      } else {
        setError('Failed to generate image')
      }
      console.error('Error generating image:', err)
    } finally {
      // Mark slot as not loading anymore
      const finalImageGenData = [...imageGenData]
      finalImageGenData[index].isLoading = false
      setImageGenData(finalImageGenData)
      setLoading(false)
    }
  }

  const handleSelectImage = async (index: number) => {
    try {
      const response = await axios.post(`/api/characters/${characterId}/select-image`, {
        image_index: index
      })
      
      // Check if the response includes the selected image path
      if (response.data.image_path) {
        // Update the character's main image in the form data
        setFormData(prev => ({
          ...prev,
          imagePath: response.data.image_path
        }))
      }
      
      navigate('/characters')
    } catch (error) {
      console.error('Error selecting image:', error)
      setError('Failed to select image')
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setRateLimitError(false)

    try {
      // Check for duplicate name first when creating
      if (mode === 'create') {
        try {
          const checkResponse = await axios.get(`/api/characters/check-name?name=${encodeURIComponent(formData.name)}`);
          if (checkResponse.data.exists) {
            setError('A character with this name already exists');
            setLoading(false);
            return;
          }
        } catch (err) {
          // If the endpoint doesn't exist, continue with creation
          console.warn('Name check endpoint not available:', err);
        }
        
        // First step: Create character with prompt
        const response = await axios.post('/api/characters/', {
          name: formData.name,
          traits: formData.traits,
        });
        
        setCharacterId(response.data.id);
        setFormData(prev => ({
          ...prev,
          imagePrompt: response.data.image_prompt
        }));

        // Initialize edited prompt
        setEditedPrompt(response.data.image_prompt);
        
        // Move to prompt edit step
        setStep('prompt-edit');
        setShowImageDialog(true);
      } else if (id) {
        await axios.put(`/api/characters/${id}`, formData);
        navigate('/characters');
      }
    } catch (err) {
      if (err instanceof AxiosError) {
        if (err.response?.status === 429) {
          setRateLimitError(true);
        } else if (err.response?.status === 409) {
          setError('A character with this name already exists');
        } else {
          setError(mode === 'create' ? 'Failed to create character' : 'Failed to update character');
        }
      }
      console.error('Error saving character:', err);
    } finally {
      setLoading(false);
    }
  }

  const handleEditPrompt = () => {
    setIsEditingPrompt(true)
  }

  const handleSavePrompt = () => {
    setFormData(prev => ({
      ...prev,
      imagePrompt: editedPrompt
    }))
    setIsEditingPrompt(false)
  }

  const handleContinueToImages = () => {
    // Initialize all image prompts with the edited prompt
    const newImageGenData = imageGenData.map(data => ({
      ...data,
      prompt: editedPrompt
    }))
    setImageGenData(newImageGenData)
    setStep('images')
  }

  const handleCloseDialog = () => {
    if (step === 'prompt-edit') {
      setShowImageDialog(false)
    } else {
      const confirmClose = window.confirm(
        'Are you sure you want to close? You can still generate images later.'
      )
      if (confirmClose) {
        setShowImageDialog(false)
        navigate('/characters')
      }
    }
  }

  const handleEnhancePrompt = async () => {
    setIsEnhancingPrompt(true);
    try {
      const response = await axios.post('/api/characters/enhance-prompt', {
        name: formData.name,
        traits: formData.traits,
        base_prompt: editedPrompt
      });
      
      setEnhancedPrompt(response.data.enhanced_prompt);
      setEditedPrompt(response.data.enhanced_prompt);
    } catch (error) {
      console.error('Error enhancing prompt:', error);
      setError('Failed to enhance prompt with GPT');
    } finally {
      setIsEnhancingPrompt(false);
    }
  };

  const renderImageSlots = () => {
    // Calculate total requests in progress
    const activeRequests = imageGenData.filter(data => data.isLoading).length;
    // Determine if we should disable buttons (based on rate limit and active requests)
    const shouldDisableButtons = !canGenerateImage() || (rateLimitInfo && (rateLimitInfo.requests <= (3 - activeRequests)));
    
    return (
      <Grid container spacing={3} sx={{ mt: 2 }}>
        {Array.from({ length: 4 }).map((_, index) => {
          const isGenerated = generatedSlots[index];
          const isLoading = imageGenData[index].isLoading;
          const imageUrl = generatedImages[index];
          const canRegenerate = !imageGenData[index].regenerationCount || imageGenData[index].regenerationCount < 1;
          
          return (
            <Grid item xs={12} sm={6} key={index}>
              <Card 
                sx={{ 
                  height: 300, 
                  display: 'flex', 
                  flexDirection: 'column', 
                  position: 'relative' 
                }}
              >
                {isGenerated ? (
                  <>
                    <CardMedia
                      component="img"
                      height="220"
                      image={imageUrl}
                      alt={`Generated image ${index}`}
                      sx={{ objectFit: 'contain' }}
                    />
                    <Box sx={{ p: 2, flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          {`DALL-E ${imageGenData[index].dalleVersion.split('-')[2]}`}
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Button 
                          variant="contained" 
                          size="small" 
                          onClick={() => handleSelectImage(index)}
                        >
                          Select
                        </Button>
                        <Tooltip title={canRegenerate ? "Regenerate this image" : "Each image can only be regenerated once"}>
                          <span>
                            <Button 
                              variant="outlined" 
                              size="small" 
                              onClick={() => handleGenerateImage(index)}
                              disabled={Boolean(isLoading || shouldDisableButtons || !canRegenerate)}
                            >
                              Regenerate {imageGenData[index].regenerationCount ? "(1/1)" : "(0/1)"}
                            </Button>
                          </span>
                        </Tooltip>
                      </Box>
                    </Box>
                  </>
                ) : (
                  <Box 
                    sx={{ 
                      p: 2, 
                      height: '100%', 
                      display: 'flex', 
                      flexDirection: 'column', 
                      justifyContent: 'space-between' 
                    }}
                  >
                    <Box>
                      <Typography variant="body1">Image {index + 1}</Typography>
                      <Box sx={{ mt: 2 }}>
                        <FormControl fullWidth size="small" sx={{ mb: 2 }}>
                          <InputLabel>DALL-E Version</InputLabel>
                          <Select
                            value={imageGenData[index].dalleVersion}
                            onChange={(e) => handleDalleVersionChange(index, e.target.value)}
                            label="DALL-E Version"
                          >
                            <MenuItem value="dall-e-2">DALL-E 2</MenuItem>
                            <MenuItem value="dall-e-3">DALL-E 3</MenuItem>
                          </Select>
                        </FormControl>
                        <TextField
                          fullWidth
                          multiline
                          rows={2}
                          size="small"
                          label="Custom prompt (optional)"
                          value={imageGenData[index].prompt || ''}
                          onChange={(e) => handlePromptChange(index, e.target.value)}
                          sx={{ mb: 2 }}
                        />
                      </Box>
                    </Box>
                    <Tooltip title={isLoading ? imageGenData[index].prompt || formData.imagePrompt || "Generating image..." : "Generate image"}>
                      <Button
                        variant="contained"
                        fullWidth
                        onClick={() => handleGenerateImage(index)}
                        disabled={Boolean(isLoading || shouldDisableButtons)}
                      >
                        {isLoading ? <CircularProgress size={24} /> : 'Generate Image'}
                      </Button>
                    </Tooltip>
                  </Box>
                )}
              </Card>
            </Grid>
          )
        })}
      </Grid>
    )
  }

  if (loading && mode === 'edit' && !formData.name) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        {mode === 'create' ? 'Create New Character' : 'Edit Character'}
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {rateLimitError && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          OpenAI API rate limit exceeded. Please wait until you can generate more images.
          {rateLimitInfo && rateLimitInfo.resetIn > 0 && (
            <Typography variant="body2">
              Rate limit resets in approximately {Math.ceil(rateLimitInfo.resetIn / 60)} minute(s).
            </Typography>
          )}
        </Alert>
      )}

      {rateLimitInfo && !rateLimitError && (
        <Alert severity="info" sx={{ mb: 2 }}>
          Image generation limit: {rateLimitInfo.requests}/3 requests remaining
        </Alert>
      )}

      <form onSubmit={handleSubmit}>
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <TextField
              required
              fullWidth
              label="Name"
              name="name"
              value={formData.name}
              onChange={handleTextChange}
            />
          </Grid>

          <Grid item xs={12}>
            <Box display="flex" gap={1}>
              <TextField
                fullWidth
                label="Add Trait"
                value={newTrait}
                onChange={(e) => setNewTrait(e.target.value)}
                onKeyPress={handleAddTrait}
                helperText="Enter traits separated by commas, spaces, or press Enter"
              />
              <Button
                variant="contained"
                onClick={handleAddTraitClick}
                disabled={!newTrait.trim()}
                sx={{ minWidth: '100px' }}
              >
                Add
              </Button>
            </Box>
          </Grid>

          <Grid item xs={12}>
            <Box display="flex" flexWrap="wrap" gap={1}>
              {formData.traits.map((trait) => (
                <Chip
                  key={trait}
                  label={trait}
                  onDelete={() => handleRemoveTrait(trait)}
                />
              ))}
            </Box>
          </Grid>

          <Grid item xs={12}>
            <Box display="flex" gap={2}>
              <Button
                type="submit"
                variant="contained"
                disabled={loading || formData.traits.length === 0}
              >
                {loading ? 'Processing...' : mode === 'create' ? 'Create Character' : 'Save Changes'}
              </Button>
              <Button
                variant="outlined"
                onClick={() => navigate('/characters')}
                disabled={loading}
              >
                Cancel
              </Button>
            </Box>
          </Grid>
        </Grid>
      </form>

      <Dialog
        open={showImageDialog}
        onClose={handleCloseDialog}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          {step === 'prompt-edit' ? 'Edit Image Prompt' : 'Generate Character Images'}
          {loading && ` (Processing...)`}
          {!canGenerateImage() && ` (Rate limit reached. Please wait.)`}
        </DialogTitle>
        <DialogContent>
          {step === 'prompt-edit' && formData.imagePrompt && (
            <Box sx={{ mt: 2 }}>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Typography variant="body1" gutterBottom>
                  Generated Prompt:
                </Typography>
                <Box>
                  {isEditingPrompt ? (
                    <IconButton onClick={handleSavePrompt} color="primary">
                      <CheckIcon />
                    </IconButton>
                  ) : (
                    <IconButton onClick={handleEditPrompt}>
                      <EditIcon />
                    </IconButton>
                  )}
                </Box>
              </Box>
              
              {isEditingPrompt ? (
                <TextField
                  fullWidth
                  multiline
                  rows={4}
                  value={editedPrompt}
                  onChange={(e) => setEditedPrompt(e.target.value)}
                  sx={{ mb: 2 }}
                />
              ) : (
                <Typography variant="body2" sx={{ p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
                  {formData.imagePrompt}
                </Typography>
              )}
              
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <Button 
                  onClick={handleEnhancePrompt} 
                  variant="outlined" 
                  startIcon={<AutoFixHighIcon />}
                  disabled={isEnhancingPrompt}
                >
                  {isEnhancingPrompt ? <CircularProgress size={24} /> : 'Enhance with GPT'}
                </Button>
                <Button 
                  onClick={() => setEditedPrompt(formData.imagePrompt || '')} 
                  color="secondary"
                >
                  Reset to Original
                </Button>
              </Box>
              
              {enhancedPrompt && (
                <Alert severity="success" sx={{ mb: 2 }}>
                  <AlertTitle>Enhanced Prompt</AlertTitle>
                  {enhancedPrompt}
                </Alert>
              )}
              
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                You can edit the prompt that will be used to generate your character images. A well-crafted prompt helps create better images.
              </Typography>
              
              <Button
                variant="contained"
                onClick={handleContinueToImages}
                sx={{ mt: 2 }}
              >
                Continue to Image Generation
              </Button>
            </Box>
          )}

          {step === 'images' && renderImageSlots()}

          {loading && step !== 'images' && (
            <Box display="flex" justifyContent="center" mt={2}>
              <CircularProgress />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>
            {step === 'prompt-edit' ? 'Cancel' : 'Close'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  )
}

export default CharacterForm 