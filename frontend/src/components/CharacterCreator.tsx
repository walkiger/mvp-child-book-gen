import React, { useState } from 'react';
import { Box, Stepper, Step, StepLabel, Typography } from '@mui/material';
import CharacterInfoStep from './CharacterInfoStep';
import CharacterTraitsStep from './CharacterTraitsStep';
import CharacterImageGrid from './CharacterImageGrid';
import { useNavigate } from 'react-router-dom';
import axios from '../lib/axios';

interface Character {
  name: string;
  traits: string[];
  images: string[];
  imagePrompt?: string;
}

const CharacterCreator = () => {
  const navigate = useNavigate();
  const [activeStep, setActiveStep] = useState(0);
  const [character, setCharacter] = useState<Character>({
    name: '',
    traits: [],
    images: [],
    imagePrompt: ''
  });
  const [error, setError] = useState<string | null>(null);

  const steps = ['Basic Info', 'Character Traits', 'Generate Images'];

  const handleNext = () => {
    setActiveStep((prevStep) => prevStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevStep) => prevStep - 1);
  };

  const handleNameSubmit = async (name: string) => {
    try {
      // Check if name exists
      const response = await axios.get(`/api/characters/check-name?name=${encodeURIComponent(name)}`);
      if (response.data.exists) {
        setError('A character with this name already exists');
        return;
      }
      if (!response.data.valid) {
        setError('Please enter a valid name (1-50 characters)');
        return;
      }
      
      setCharacter(prev => ({ ...prev, name }));
      setError(null);
      handleNext();
    } catch (err) {
      setError('Failed to validate character name');
    }
  };

  const handleTraitsSubmit = (traits: string[]) => {
    setCharacter(prev => ({ ...prev, traits }));
    handleNext();
  };

  const handleImagesSubmit = async (images: string[]) => {
    try {
      // Create character with generated images
      const response = await axios.post('/api/characters', {
        name: character.name,
        traits: character.traits,
        generated_images: images
      });
      
      // Navigate to character list or detail page
      navigate('/characters');
    } catch (err) {
      setError('Failed to save character');
    }
  };

  const renderStep = () => {
    switch (activeStep) {
      case 0:
        return (
          <CharacterInfoStep 
            name={character.name}
            onSubmit={handleNameSubmit}
            error={error}
          />
        );
      case 1:
        return (
          <CharacterTraitsStep 
            traits={character.traits}
            onSubmit={handleTraitsSubmit}
            onBack={handleBack}
          />
        );
      case 2:
        return (
          <CharacterImageGrid 
            character={character}
            onSave={handleImagesSubmit}
            onBack={handleBack}
          />
        );
      default:
        return null;
    }
  };

  return (
    <Box sx={{ width: '100%', p: 3 }}>
      <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
        {steps.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>
      
      {error && (
        <Typography color="error" sx={{ mb: 2 }}>
          {error}
        </Typography>
      )}
      
      {renderStep()}
    </Box>
  );
};

export default CharacterCreator; 