import React, { useState } from 'react'
import { Link as RouterLink, useNavigate } from 'react-router-dom'
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  IconButton,
  Menu,
  MenuItem,
  Box,
  Avatar
} from '@mui/material'
import MenuIcon from '@mui/icons-material/Menu'
import useAuth from '../hooks/useAuth'

const Navbar: React.FC = () => {
  const { isAuthenticated, logout, user } = useAuth()
  const navigate = useNavigate()
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)
  const [mobileAnchorEl, setMobileAnchorEl] = useState<null | HTMLElement>(null)

  const handleMenu = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget)
  }

  const handleMobileMenu = (event: React.MouseEvent<HTMLElement>) => {
    setMobileAnchorEl(event.currentTarget)
  }

  const handleClose = () => {
    setAnchorEl(null)
  }

  const handleMobileClose = () => {
    setMobileAnchorEl(null)
  }

  const handleLogout = () => {
    logout()
    navigate('/login')
    handleClose()
    handleMobileClose()
  }

  return (
    <AppBar position="static">
      <Toolbar>
        <Typography
          variant="h6"
          component={RouterLink}
          to="/"
          sx={{
            flexGrow: 1,
            textDecoration: 'none',
            color: 'white',
          }}
        >
          Child Book Generator
        </Typography>

        {/* Mobile menu */}
        <Box sx={{ display: { xs: 'flex', md: 'none' } }}>
          <IconButton
            size="large"
            aria-label="account of current user"
            aria-controls="menu-appbar"
            aria-haspopup="true"
            onClick={handleMobileMenu}
            color="inherit"
          >
            <MenuIcon />
          </IconButton>
          <Menu
            id="menu-appbar-mobile"
            anchorEl={mobileAnchorEl}
            anchorOrigin={{
              vertical: 'top',
              horizontal: 'right',
            }}
            keepMounted
            transformOrigin={{
              vertical: 'top',
              horizontal: 'right',
            }}
            open={Boolean(mobileAnchorEl)}
            onClose={handleMobileClose}
          >
            {isAuthenticated ? (
              <>
                <MenuItem onClick={handleMobileClose} component={RouterLink} to="/story-builder">Story Builder</MenuItem>
                <MenuItem onClick={handleMobileClose} component={RouterLink} to="/stories">My Stories</MenuItem>
                <MenuItem onClick={handleMobileClose} component={RouterLink} to="/characters">Characters</MenuItem>
                <MenuItem onClick={handleLogout}>Logout</MenuItem>
              </>
            ) : (
              <>
                <MenuItem onClick={handleMobileClose} component={RouterLink} to="/login">Login</MenuItem>
                <MenuItem onClick={handleMobileClose} component={RouterLink} to="/register">Register</MenuItem>
              </>
            )}
          </Menu>
        </Box>

        {/* Desktop menu */}
        <Box sx={{ display: { xs: 'none', md: 'flex' }, alignItems: 'center' }}>
          {isAuthenticated ? (
            <>
              <Button color="inherit" component={RouterLink} to="/story-builder">
                Story Builder
              </Button>
              <Button color="inherit" component={RouterLink} to="/stories">
                My Stories
              </Button>
              <Button color="inherit" component={RouterLink} to="/characters">
                Characters
              </Button>
              <Box sx={{ ml: 2 }}>
                <IconButton onClick={handleMenu} sx={{ p: 0 }}>
                  <Avatar alt={user?.username} src="/static/images/avatar/1.jpg" />
                </IconButton>
                <Menu
                  id="menu-appbar"
                  anchorEl={anchorEl}
                  anchorOrigin={{
                    vertical: 'top',
                    horizontal: 'right',
                  }}
                  keepMounted
                  transformOrigin={{
                    vertical: 'top',
                    horizontal: 'right',
                  }}
                  open={Boolean(anchorEl)}
                  onClose={handleClose}
                >
                  <MenuItem component={RouterLink} to="/profile" onClick={handleClose}>Profile</MenuItem>
                  <MenuItem onClick={handleLogout}>Logout</MenuItem>
                </Menu>
              </Box>
            </>
          ) : (
            <>
              <Button color="inherit" component={RouterLink} to="/login">
                Login
              </Button>
              <Button color="inherit" component={RouterLink} to="/register">
                Register
              </Button>
            </>
          )}
        </Box>
      </Toolbar>
    </AppBar>
  )
}

export default Navbar 