import React, { useState } from 'react';
import { 
  Box, 
  Chip, 
  TextField, 
  Button, 
  Typography,
  Stack
} from '@mui/material';

interface CharacterTraitsStepProps {
  traits: string[];
  onSubmit: (traits: string[]) => void;
  onBack: () => void;
}

const CharacterTraitsStep = ({ traits, onSubmit, onBack }: CharacterTraitsStepProps) => {
  const [localTraits, setLocalTraits] = useState<string[]>(traits);
  const [newTrait, setNewTrait] = useState('');

  const handleAddTrait = () => {
    if (newTrait.trim() && !localTraits.includes(newTrait.trim())) {
      setLocalTraits([...localTraits, newTrait.trim()]);
      setNewTrait('');
    }
  };

  const handleDeleteTrait = (traitToDelete: string) => {
    setLocalTraits(localTraits.filter(trait => trait !== traitToDelete));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(localTraits);
  };

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ maxWidth: 600, mx: 'auto' }}>
      <Typography variant="h6" gutterBottom>
        What traits does your character have?
      </Typography>
      
      <Box sx={{ mb: 3 }}>
        <TextField
          fullWidth
          label="Add a trait"
          value={newTrait}
          onChange={(e) => setNewTrait(e.target.value)}
          onKeyPress={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault();
              handleAddTrait();
            }
          }}
          sx={{ mb: 2 }}
        />
        
        <Button
          variant="outlined"
          onClick={handleAddTrait}
          disabled={!newTrait.trim()}
          sx={{ mb: 2 }}
        >
          Add Trait
        </Button>
      </Box>
      
      <Box sx={{ mb: 3 }}>
        <Typography variant="subtitle2" gutterBottom>
          Current Traits:
        </Typography>
        <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
          {localTraits.map((trait) => (
            <Chip
              key={trait}
              label={trait}
              onDelete={() => handleDeleteTrait(trait)}
              sx={{ m: 0.5 }}
            />
          ))}
        </Stack>
      </Box>
      
      <Stack direction="row" spacing={2}>
        <Button onClick={onBack}>
          Back
        </Button>
        <Button
          variant="contained"
          type="submit"
          disabled={localTraits.length === 0}
        >
          Continue
        </Button>
      </Stack>
    </Box>
  );
};

export default CharacterTraitsStep; 