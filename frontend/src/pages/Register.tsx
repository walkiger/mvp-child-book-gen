import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Container,
  Box,
  Typography,
  TextField,
  Button,
  Alert,
  Paper,
  List,
  ListItem,
  ListItemText,
  FormControl,
  Stack,
} from '@mui/material'
import useAuth from '../hooks/useAuth'
import { APIError } from '../lib/errorHandling'

interface FieldError {
  [key: string]: string;
}

interface PasswordValidation {
  hasMinLength: boolean;
  hasLetter: boolean;
  hasNumber: boolean;
}

const Register = () => {
  const navigate = useNavigate()
  const { register } = useAuth()
  const [error, setError] = useState<string>('')
  const [fieldErrors, setFieldErrors] = useState<FieldError>({})
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [passwordValidation, setPasswordValidation] = useState<PasswordValidation>({
    hasMinLength: false,
    hasLetter: false,
    hasNumber: false,
  })
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    first_name: '',
    last_name: '',
  })

  const validatePassword = (password: string) => {
    setPasswordValidation({
      hasMinLength: password.length >= 8,
      hasLetter: /[A-Za-z]/.test(password),
      hasNumber: /\d/.test(password),
    })
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
    
    // Update password validation UI
    if (name === 'password') {
      validatePassword(value)
    }
    
    // Clear errors when user starts typing
    if (fieldErrors[name]) {
      setFieldErrors((prev) => {
        const newErrors = { ...prev }
        delete newErrors[name]
        return newErrors
      })
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setFieldErrors({})
    setSuggestions([])

    if (formData.password !== formData.confirmPassword) {
      setFieldErrors({
        confirmPassword: 'Passwords do not match',
        password: 'Passwords do not match'
      })
      return
    }

    try {
      const userData = {
        email: formData.email,
        password: formData.password,
        username: formData.username,
        first_name: formData.first_name,
        last_name: formData.last_name
      }
      await register(userData)
      navigate('/generate')
    } catch (err) {
      const apiError = err as APIError
      if (apiError.error_code?.startsWith('VAL-AUTH')) {
        // Handle validation errors
        const newFieldErrors: FieldError = {}
        
        if (apiError.additional_data) {
          // Map backend field errors to form fields
          Object.entries(apiError.additional_data).forEach(([key, value]) => {
            if (key in formData) {
              newFieldErrors[key] = value as string
            }
          })
        }
        
        setFieldErrors(newFieldErrors)
        if (apiError.suggestions?.length) {
          setSuggestions(apiError.suggestions)
        }
        setError(apiError.message)
      } else {
        // Handle general errors
        setError(apiError.message || 'Registration failed. Please try again.')
        if (apiError.suggestions?.length) {
          setSuggestions(apiError.suggestions)
        }
      }
    }
  }

  return (
    <Container maxWidth="sm">
      <Box
        sx={{
          mt: 8,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        <Paper
          elevation={3}
          sx={{
            p: 4,
            width: '100%',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
          }}
        >
          <Typography component="h1" variant="h4" gutterBottom>
            Register
          </Typography>
          {error && (
            <Alert severity="error" sx={{ width: '100%', mb: 2 }}>
              {error}
              {suggestions.length > 0 && (
                <List dense>
                  {suggestions.map((suggestion, index) => (
                    <ListItem key={index}>
                      <ListItemText primary={suggestion} />
                    </ListItem>
                  ))}
                </List>
              )}
            </Alert>
          )}
          <Box component="form" onSubmit={handleSubmit} sx={{ width: '100%' }}>
            <TextField
              margin="normal"
              required
              fullWidth
              id="username"
              label="Username"
              name="username"
              autoComplete="username"
              autoFocus
              value={formData.username}
              onChange={handleChange}
              error={!!fieldErrors.username}
              helperText={fieldErrors.username}
            />
            <TextField
              margin="normal"
              required
              fullWidth
              id="email"
              label="Email Address"
              name="email"
              autoComplete="email"
              value={formData.email}
              onChange={handleChange}
              error={!!fieldErrors.email}
              helperText={fieldErrors.email}
            />
            <TextField
              margin="normal"
              required
              fullWidth
              id="first_name"
              label="First Name"
              name="first_name"
              autoComplete="given-name"
              value={formData.first_name}
              onChange={handleChange}
              error={!!fieldErrors.first_name}
              helperText={fieldErrors.first_name}
            />
            <TextField
              margin="normal"
              required
              fullWidth
              id="last_name"
              label="Last Name"
              name="last_name"
              autoComplete="family-name"
              value={formData.last_name}
              onChange={handleChange}
              error={!!fieldErrors.last_name}
              helperText={fieldErrors.last_name}
            />
            <FormControl fullWidth margin="normal" error={!!fieldErrors.password}>
              <TextField
                required
                fullWidth
                name="password"
                label="Password"
                type="password"
                id="password"
                autoComplete="new-password"
                value={formData.password}
                onChange={handleChange}
                error={!!fieldErrors.password}
              />
              <Box sx={{ mt: 1 }}>
                <Typography variant="caption" color="textSecondary">
                  Password requirements:
                </Typography>
                <Stack spacing={0.5}>
                  <Typography
                    variant="caption"
                    sx={{
                      color: passwordValidation.hasMinLength ? 'success.main' : 'text.secondary',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 0.5,
                    }}
                  >
                    • At least 8 characters {passwordValidation.hasMinLength ? '✓' : ''}
                  </Typography>
                  <Typography
                    variant="caption"
                    sx={{
                      color: passwordValidation.hasLetter ? 'success.main' : 'text.secondary',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 0.5,
                    }}
                  >
                    • At least one letter {passwordValidation.hasLetter ? '✓' : ''}
                  </Typography>
                  <Typography
                    variant="caption"
                    sx={{
                      color: passwordValidation.hasNumber ? 'success.main' : 'text.secondary',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 0.5,
                    }}
                  >
                    • At least one number {passwordValidation.hasNumber ? '✓' : ''}
                  </Typography>
                </Stack>
                {fieldErrors.password && (
                  <Typography color="error" variant="caption" sx={{ display: 'block', mt: 1 }}>
                    {fieldErrors.password}
                  </Typography>
                )}
              </Box>
            </FormControl>
            <TextField
              margin="normal"
              required
              fullWidth
              name="confirmPassword"
              label="Confirm Password"
              type="password"
              id="confirmPassword"
              autoComplete="new-password"
              value={formData.confirmPassword}
              onChange={handleChange}
              error={!!fieldErrors.confirmPassword}
              helperText={fieldErrors.confirmPassword}
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3, mb: 2 }}
            >
              Register
            </Button>
          </Box>
        </Paper>
      </Box>
    </Container>
  )
}

export default Register 