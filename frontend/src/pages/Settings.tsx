import React, { useState, useEffect } from 'react';
import {
  Container,
  Box,
  Typography,
  Paper,
  Grid,
  Switch,
  FormControlLabel,
  Button,
  Divider,
  Alert,
} from '@mui/material';
import useAuth from '../hooks/useAuth';
import axios from '../lib/axios';
import LoadingState from '../components/LoadingState';
import ErrorDisplay from '../components/ErrorDisplay';
import { ApiError, formatApiError, retryOperation } from '../lib/errorHandling';

interface UserSettings {
  email_notifications: boolean;
  theme_preference: 'light' | 'dark';
  language_preference: string;
  story_privacy_default: 'public' | 'private';
  auto_save_interval: number;
}

const Settings: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const [settings, setSettings] = useState<UserSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const [successMessage, setSuccessMessage] = useState<string>('');

  const fetchSettings = async () => {
    try {
      const response = await retryOperation(async () => {
        const res = await axios.get('/api/users/settings');
        if (!res.data) {
          throw new Error('No data received from server');
        }
        return res;
      });

      setSettings(response.data);
      setError(null);
    } catch (err) {
      const apiError = formatApiError(err);
      setError(apiError);
      console.error('Error fetching settings:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchSettings();
    }
  }, [isAuthenticated]);

  const handleSettingChange = (setting: keyof UserSettings) => (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    if (settings) {
      setSettings({
        ...settings,
        [setting]: event.target.checked,
      });
    }
  };

  const handleSave = async () => {
    if (!settings) return;

    setSaving(true);
    setError(null);
    setSuccessMessage('');

    try {
      const response = await retryOperation(async () => {
        const res = await axios.patch('/api/users/settings', settings);
        if (!res.data) {
          throw new Error('No data received from server');
        }
        return res;
      });

      setSettings(response.data);
      setSuccessMessage('Settings saved successfully!');
      setError(null);
    } catch (err) {
      const apiError = formatApiError(err);
      setError(apiError);
      console.error('Error saving settings:', err);
    } finally {
      setSaving(false);
    }
  };

  if (!isAuthenticated) {
    return (
      <Container maxWidth="sm">
        <Box sx={{ mt: 8, textAlign: 'center' }}>
          <Typography variant="h5" gutterBottom>
            Please log in to view settings
          </Typography>
        </Box>
      </Container>
    );
  }

  if (loading) {
    return <LoadingState variant="spinner" text="Loading settings..." />;
  }

  return (
    <Container maxWidth="md">
      <Box sx={{ mt: 8, mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          Settings
        </Typography>

        {error && (
          <ErrorDisplay 
            error={error} 
            onRetry={error.retry ? fetchSettings : undefined}
          />
        )}

        {successMessage && (
          <Alert severity="success" sx={{ mb: 3 }}>
            {successMessage}
          </Alert>
        )}

        <Paper elevation={3} sx={{ p: 4 }}>
          <Typography variant="h6" gutterBottom>
            Notifications
          </Typography>
          <FormControlLabel
            control={
              <Switch
                checked={settings?.email_notifications || false}
                onChange={handleSettingChange('email_notifications')}
                disabled={saving}
              />
            }
            label="Email Notifications"
          />

          <Divider sx={{ my: 3 }} />

          <Typography variant="h6" gutterBottom>
            Privacy
          </Typography>
          <FormControlLabel
            control={
              <Switch
                checked={settings?.story_privacy_default === 'private'}
                onChange={(e) =>
                  settings &&
                  setSettings({
                    ...settings,
                    story_privacy_default: e.target.checked ? 'private' : 'public',
                  })
                }
                disabled={saving}
              />
            }
            label="Make new stories private by default"
          />

          <Divider sx={{ my: 3 }} />

          <Typography variant="h6" gutterBottom>
            Auto-save
          </Typography>
          <FormControlLabel
            control={
              <Switch
                checked={(settings?.auto_save_interval ?? 0) > 0}
                onChange={(e) =>
                  settings &&
                  setSettings({
                    ...settings,
                    auto_save_interval: e.target.checked ? 300000 : 0, // 5 minutes in milliseconds
                  })
                }
                disabled={saving}
              />
            }
            label="Enable auto-save (every 5 minutes)"
          />

          <Box sx={{ mt: 4, display: 'flex', justifyContent: 'flex-end' }}>
            <Button
              variant="contained"
              onClick={handleSave}
              disabled={saving}
            >
              {saving ? (
                <LoadingState variant="spinner" text="Saving..." height={24} />
              ) : (
                'Save Changes'
              )}
            </Button>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
};

export default Settings; 