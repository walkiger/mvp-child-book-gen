import React, { useState, useEffect } from 'react';
import { Container, Typography, Box, Paper, Stepper, Step, StepLabel, Button } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import axios from '../lib/axios';
import LoadingState from '../components/LoadingState';
import ErrorDisplay from '../components/ErrorDisplay';
import { ApiError, formatApiError, retryOperation } from '../lib/errorHandling';

const steps = ['Select Character', 'Story Details', 'Generate Story'];

interface StoryBuilderState {
  currentStep: number;
  loading: boolean;
  error: ApiError | null;
  storyData: {
    character_id?: number;
    title?: string;
    age_group?: string;
    theme?: string;
    moral_lesson?: string;
  };
}

const StoryBuilder: React.FC = () => {
  const navigate = useNavigate();
  const [state, setState] = useState<StoryBuilderState>({
    currentStep: 0,
    loading: false,
    error: null,
    storyData: {},
  });

  const handleNext = async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    try {
      // Validate current step
      await validateStep();
      
      if (state.currentStep === steps.length - 1) {
        // Generate story
        await generateStory();
      } else {
        // Move to next step
        setState(prev => ({
          ...prev,
          currentStep: prev.currentStep + 1,
          loading: false,
        }));
      }
    } catch (err) {
      setState(prev => ({
        ...prev,
        error: formatApiError(err),
        loading: false,
      }));
    }
  };

  const handleBack = () => {
    setState(prev => ({
      ...prev,
      currentStep: prev.currentStep - 1,
      error: null,
    }));
  };

  const validateStep = async () => {
    const { currentStep, storyData } = state;
    
    switch (currentStep) {
      case 0:
        if (!storyData.character_id) {
          throw new Error('Please select a character');
        }
        break;
      case 1:
        if (!storyData.title?.trim()) {
          throw new Error('Please enter a story title');
        }
        if (!storyData.age_group) {
          throw new Error('Please select an age group');
        }
        break;
      // Add more validation as needed
    }
  };

  const generateStory = async () => {
    try {
      const response = await retryOperation(async () => {
        const res = await axios.post('/api/stories/generate', state.storyData);
        if (!res.data) {
          throw new Error('No data received from server');
        }
        return res;
      });

      // Navigate to the new story
      navigate(`/stories/${response.data.id}`);
    } catch (err) {
      setState(prev => ({
        ...prev,
        error: formatApiError(err),
        loading: false,
      }));
    }
  };

  const getStepContent = (step: number) => {
    switch (step) {
      case 0:
        return 'Select a character for your story';
      case 1:
        return 'Enter story details and preferences';
      case 2:
        return 'Review and generate your story';
      default:
        return 'Unknown step';
    }
  };

  return (
    <Container maxWidth="md">
      <Box sx={{ mt: 4, mb: 4 }}>
        <Paper elevation={3} sx={{ p: 4 }}>
          <Typography component="h1" variant="h4" align="center" gutterBottom>
            Create a New Story
          </Typography>

          {state.error && (
            <Box sx={{ mb: 3 }}>
              <ErrorDisplay 
                error={state.error}
                onRetry={state.currentStep === steps.length - 1 ? generateStory : undefined}
              />
            </Box>
          )}

          <Stepper activeStep={state.currentStep} sx={{ mb: 4 }}>
            {steps.map((label) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>

          {state.loading ? (
            <LoadingState 
              variant="spinner" 
              text={state.currentStep === steps.length - 1 ? 'Generating story...' : 'Loading...'} 
            />
          ) : (
            <>
              <Typography variant="body1" sx={{ mb: 4 }}>
                {getStepContent(state.currentStep)}
              </Typography>

              {/* Step content will be rendered here */}

              <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 4 }}>
                <Button
                  variant="outlined"
                  onClick={handleBack}
                  sx={{ mr: 1 }}
                  disabled={state.currentStep === 0}
                >
                  Back
                </Button>
                <Button
                  variant="contained"
                  onClick={handleNext}
                  disabled={state.loading}
                >
                  {state.currentStep === steps.length - 1 ? 'Generate Story' : 'Next'}
                </Button>
              </Box>
            </>
          )}
        </Paper>
      </Box>
    </Container>
  );
};

export default StoryBuilder; 