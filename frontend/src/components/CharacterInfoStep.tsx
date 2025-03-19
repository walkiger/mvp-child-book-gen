import React, { useState } from 'react';
import { Box, TextField, Button, Typography } from '@mui/material';

interface CharacterInfoStepProps {
  name: string;
  onSubmit: (name: string) => void;
  error?: string | null;
}

const CharacterInfoStep = ({ name, onSubmit, error }: CharacterInfoStepProps) => {
  const [localName, setLocalName] = useState(name);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(localName.trim());
  };

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ maxWidth: 400, mx: 'auto' }}>
      <Typography variant="h6" gutterBottom>
        What's your character's name?
      </Typography>
      
      <TextField
        fullWidth
        label="Character Name"
        value={localName}
        onChange={(e) => setLocalName(e.target.value)}
        error={!!error}
        helperText={error || 'Enter a name for your character (1-50 characters)'}
        sx={{ mb: 3 }}
      />
      
      <Button
        variant="contained"
        type="submit"
        disabled={!localName.trim()}
        fullWidth
      >
        Continue
      </Button>
    </Box>
  );
};

export default CharacterInfoStep; 