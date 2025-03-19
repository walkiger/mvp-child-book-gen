import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Paper,
  Button,
  Typography,
  IconButton,
  TextField,
  CircularProgress,
  Stack,
  Alert
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import RefreshIcon from '@mui/icons-material/Refresh';
import EditIcon from '@mui/icons-material/Edit';
import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh';
import axios from '../lib/axios';
import AuthenticatedImage from './AuthenticatedImage';

interface CharacterImageGridProps {
  character: {
    name: string;
    traits: string[];
  };
  onSave: (images: string[]) => void;
  onBack: () => void;
}

const CharacterImageGrid = ({ character, onSave, onBack }: CharacterImageGridProps) => {
  const [images, setImages] = useState<(string | null)[]>(new Array(4).fill(null));
  const [loading, setLoading] = useState<number[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [prompt, setPrompt] = useState<string>('');
  const [isEditingPrompt, setIsEditingPrompt] = useState(false);
  const [isRefiningPrompt, setIsRefiningPrompt] = useState(false);

  useEffect(() => {
    generateInitialPrompt();
  }, []);

  const generateInitialPrompt = async () => {
    try {
      const response = await axios.post('/api/characters/generate-prompt', {
        name: character.name,
        traits: character.traits
      });
      setPrompt(response.data.prompt);
    } catch (err) {
      setError('Failed to generate initial prompt');
    }
  };

  const refinePrompt = async () => {
    try {
      setIsRefiningPrompt(true);
      const response = await axios.post('/api/characters/refine-prompt', {
        name: character.name,
        traits: character.traits,
        base_prompt: prompt
      });
      setPrompt(response.data.enhanced_prompt);
    } catch (err) {
      setError('Failed to refine prompt');
    } finally {
      setIsRefiningPrompt(false);
    }
  };

  const generateImage = async (index: number) => {
    try {
      setLoading(prev => [...prev, index]);
      setError(null);

      const response = await axios.post(`/api/characters/generate-image`, {
        index,
        prompt,
        dalle_version: 'dall-e-3'
      });

      setImages(prev => {
        const newImages = [...prev];
        newImages[index] = response.data.image_url;
        return newImages;
      });
    } catch (err) {
      setError('Failed to generate image');
    } finally {
      setLoading(prev => prev.filter(i => i !== index));
    }
  };

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto' }}>
      <Typography variant="h6" gutterBottom>
        Generate Images for {character.name}
      </Typography>

      {/* Prompt Section */}
      <Paper sx={{ p: 2, mb: 3, backgroundColor: '#f5f5f5' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <Typography variant="subtitle1" sx={{ mr: 2 }}>
            Image Generation Prompt:
          </Typography>
          <Button
            size="small"
            onClick={() => setIsEditingPrompt(true)}
            startIcon={<EditIcon />}
            sx={{ mr: 1 }}
          >
            Edit
          </Button>
          <Button
            size="small"
            onClick={refinePrompt}
            startIcon={<AutoFixHighIcon />}
            disabled={isRefiningPrompt}
          >
            Refine with AI
          </Button>
        </Box>

        {isEditingPrompt ? (
          <Box sx={{ display: 'flex', gap: 1 }}>
            <TextField
              fullWidth
              multiline
              rows={3}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
            />
            <Button
              onClick={() => setIsEditingPrompt(false)}
              variant="contained"
              sx={{ alignSelf: 'flex-end' }}
            >
              Save
            </Button>
          </Box>
        ) : (
          <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
            {prompt || 'Generating prompt...'}
          </Typography>
        )}
      </Paper>

      {/* Image Grid */}
      <Grid container spacing={2}>
        {images.map((image, index) => (
          <Grid item xs={12} sm={6} key={index}>
            <Paper
              sx={{
                aspectRatio: '1',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
                position: 'relative'
              }}
              onClick={() => !loading.includes(index) && !image && generateImage(index)}
            >
              {image ? (
                <>
                  <AuthenticatedImage
                    src={image}
                    alt={`${character.name} - ${index + 1}`}
                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                  />
                  <IconButton
                    sx={{ position: 'absolute', top: 8, right: 8 }}
                    onClick={(e) => {
                      e.stopPropagation();
                      generateImage(index);
                    }}
                  >
                    <RefreshIcon />
                  </IconButton>
                </>
              ) : loading.includes(index) ? (
                <CircularProgress />
              ) : (
                <Box sx={{ textAlign: 'center' }}>
                  <AddIcon sx={{ fontSize: 40 }} />
                  <Typography variant="caption" display="block">
                    Generate Image {index + 1}
                  </Typography>
                </Box>
              )}
            </Paper>
          </Grid>
        ))}
      </Grid>

      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}

      <Stack direction="row" spacing={2} sx={{ mt: 3 }}>
        <Button onClick={onBack}>
          Back
        </Button>
        <Button
          variant="contained"
          onClick={() => onSave(images.filter((img): img is string => img !== null))}
          disabled={!images.some(img => img) || loading.length > 0}
        >
          Save Character
        </Button>
      </Stack>
    </Box>
  );
};

export default CharacterImageGrid; 