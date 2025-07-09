# AI Podcast Generator

## Overview

This is a Flask-based web application that generates AI-powered podcasts. Users can sign up, log in, and convert text content into professional-sounding audio podcasts using the Play HT text-to-speech API. The application features a modern, Spotify-inspired UI design and provides a complete podcast generation workflow.

## System Architecture

The application follows a traditional Flask web application architecture with the following layers:

- **Frontend**: Server-side rendered HTML templates with Bootstrap CSS framework and custom styling
- **Backend**: Flask web framework with SQLAlchemy ORM for database operations
- **Database**: SQLite (development) with SQLAlchemy models for user and podcast data
- **External API**: Play HT API integration for text-to-speech conversion
- **Authentication**: Flask-Login for session management and user authentication

## Key Components

### Core Application Files
- **app.py**: Main Flask application setup, database configuration, and Flask-Login initialization
- **main.py**: Application entry point that runs the Flask development server
- **models.py**: SQLAlchemy database models for User and Podcast entities
- **routes.py**: Flask route handlers for authentication and podcast generation
- **playht_service.py**: Service class for Play HT API integration

### Frontend Components
- **templates/**: Jinja2 HTML templates with Bootstrap-based UI
  - **base.html**: Base template with navigation and common layout
  - **home.html**: Landing page with hero section and features
  - **signin.html** / **signup.html**: Authentication forms
  - **generator.html**: Podcast creation interface
- **static/css/styles.css**: Custom CSS with Spotify-inspired design system
- **static/js/main.js**: Client-side JavaScript for form validation and interactions

### Database Schema
- **User Model**: Authentication and user management (id, username, email, password_hash, created_at)
- **Podcast Model**: Podcast episodes with generation status tracking (id, title, description, content, audio_url, playht_job_id, status, created_at, user_id)

## Data Flow

1. **User Registration/Login**: Users create accounts or authenticate using email/password
2. **Podcast Creation**: Authenticated users submit text content through the generator form
3. **Text-to-Speech Processing**: Content is sent to Play HT API for audio generation
4. **Status Tracking**: Podcast generation status is tracked (pending, processing, completed, failed)
5. **Audio Delivery**: Generated audio URLs are stored and made available to users

## External Dependencies

### Required APIs
- **Play HT API**: Text-to-speech conversion service
  - Requires `PLAYHT_API_KEY` and `PLAYHT_USER_ID` environment variables
  - Supports multiple voice options and audio quality settings

### Python Dependencies
- **Flask**: Web framework
- **Flask-SQLAlchemy**: Database ORM
- **Flask-Login**: User session management
- **Werkzeug**: Security utilities for password hashing
- **Requests**: HTTP client for external API calls

### Frontend Dependencies
- **Bootstrap 5.3.0**: CSS framework
- **Font Awesome 6.4.0**: Icon library
- **Google Fonts (Inter)**: Typography

## Deployment Strategy

The application is configured for deployment with:

- **Environment Variables**: 
  - `SESSION_SECRET`: Flask session security
  - `DATABASE_URL`: Database connection string
  - `PLAYHT_API_KEY` and `PLAYHT_USER_ID`: Play HT API credentials
- **Database**: SQLite for development, configurable for production databases
- **WSGI**: ProxyFix middleware for deployment behind reverse proxies
- **Static Files**: Served through Flask's static file handling

The application uses SQLAlchemy's pool configuration for database connection management and includes logging for debugging and monitoring.

## User Preferences

Preferred communication style: Simple, everyday language.

## Changelog

Changelog:
- July 05, 2025. Initial setup
- July 09, 2025. Updated PlayHT API integration to use v1 endpoints as per official documentation. Added dynamic voice loading with proper language grouping and search functionality. Enhanced voice selection UI with descriptions and language filtering.