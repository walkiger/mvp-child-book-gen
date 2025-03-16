import React, { useState, useEffect } from 'react';
import {
  Container,
  Box,
  Typography,
  Paper,
  Grid,
  TextField,
  Button,
  Avatar,
  IconButton,
  Alert,
} from '@mui/material';
import PhotoCamera from '@mui/icons-material/PhotoCamera';
import useAuth from '../hooks/useAuth';
import axios from '../lib/axios';
import LoadingState from '../components/LoadingState';
import ErrorDisplay from '../components/ErrorDisplay';
import { ApiError, formatApiError, retryOperation } from '../lib/errorHandling';

interface UserProfile {
  id: number;
  username: string;
  email: string;
  full_name: string;
  avatar_url: string;
  created_at: string;
  stories_count: number;
  characters_count: number;
}

interface FormData {
  full_name: string;
  email: string;
  avatar?: File;
}

const UserProfile: React.FC = () => {
  const { isAuthenticated, user } = useAuth();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const [editMode, setEditMode] = useState(false);
  const [formData, setFormData] = useState<FormData>({
    full_name: '',
    email: '',
  });
  const [successMessage, setSuccessMessage] = useState<string>('');

  const fetchProfile = async () => {
    try {
      const response = await retryOperation(async () => {
        const res = await axios.get('/api/users/profile');
        if (!res.data) {
          throw new Error('No data received from server');
        }
        return res;
      });

      setProfile(response.data);
      setFormData({
        full_name: response.data.full_name,
        email: response.data.email,
      });
      setError(null);
    } catch (err) {
      setError(formatApiError(err));
      console.error('Error fetching profile:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchProfile();
    }
  }, [isAuthenticated]);

  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = event.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleAvatarChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      setFormData((prev) => ({
        ...prev,
        avatar: event.target.files![0],
      }));
    }
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setSaving(true);
    setError(null);
    setSuccessMessage('');

    try {
      const formDataToSend = new FormData();
      formDataToSend.append('full_name', formData.full_name);
      formDataToSend.append('email', formData.email);
      if (formData.avatar) {
        formDataToSend.append('avatar', formData.avatar);
      }

      const response = await retryOperation(async () => {
        const res = await axios.patch('/api/users/profile', formDataToSend, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
        if (!res.data) {
          throw new Error('No data received from server');
        }
        return res;
      });

      setProfile(response.data);
      setEditMode(false);
      setSuccessMessage('Profile updated successfully!');
      setError(null);
    } catch (err) {
      setError(formatApiError(err));
      console.error('Error updating profile:', err);
    } finally {
      setSaving(false);
    }
  };

  if (!isAuthenticated) {
    return (
      <Container maxWidth="sm">
        <Box sx={{ mt: 8, textAlign: 'center' }}>
          <Typography variant="h5" gutterBottom>
            Please log in to view your profile
          </Typography>
        </Box>
      </Container>
    );
  }

  if (loading) {
    return <LoadingState variant="spinner" text="Loading profile..." />;
  }

  return (
    <Container maxWidth="md">
      <Box sx={{ mt: 8, mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          Profile
        </Typography>

        {error && (
          <Box sx={{ mb: 3 }}>
            <ErrorDisplay 
              error={error} 
              onRetry={error.retry ? fetchProfile : undefined}
            />
          </Box>
        )}

        {successMessage && (
          <Box sx={{ mb: 3 }}>
            <Alert severity="success">{successMessage}</Alert>
          </Box>
        )}

        <Paper elevation={3} sx={{ p: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 4 }}>
            <Avatar
              src={profile?.avatar_url}
              alt={profile?.full_name}
              sx={{ width: 100, height: 100, mr: 2 }}
            />
            {editMode && (
              <label htmlFor="avatar-input">
                <input
                  type="file"
                  id="avatar-input"
                  accept="image/*"
                  style={{ display: 'none' }}
                  onChange={handleAvatarChange}
                  disabled={saving}
                />
                <IconButton
                  color="primary"
                  component="span"
                  disabled={saving}
                >
                  <PhotoCamera />
                </IconButton>
              </label>
            )}
          </Box>

          <Box component="form" onSubmit={handleSubmit}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Full Name"
                  name="full_name"
                  value={editMode ? formData.full_name : profile?.full_name}
                  onChange={handleInputChange}
                  disabled={!editMode || saving}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Email"
                  name="email"
                  type="email"
                  value={editMode ? formData.email : profile?.email}
                  onChange={handleInputChange}
                  disabled={!editMode || saving}
                />
              </Grid>
            </Grid>

            <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
              {editMode ? (
                <>
                  <Button
                    variant="outlined"
                    onClick={() => setEditMode(false)}
                    disabled={saving}
                  >
                    Cancel
                  </Button>
                  <Button
                    variant="contained"
                    type="submit"
                    disabled={saving}
                  >
                    {saving ? (
                      <LoadingState variant="spinner" text="Saving..." height={24} />
                    ) : (
                      'Save Changes'
                    )}
                  </Button>
                </>
              ) : (
                <Button
                  variant="contained"
                  onClick={() => setEditMode(true)}
                >
                  Edit Profile
                </Button>
              )}
            </Box>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
};

export default UserProfile; 