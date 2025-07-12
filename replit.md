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

#### New Neon Database Tables (PostgreSQL)
- **Users Table**: Enhanced user management with subscription support
  - id, username, email, password_hash, stripe_customer_id, plan_status (free/pro/elite), expires_at, created_at
  - Includes plan limits and subscription management methods

- **Usage Table**: Token usage tracking for AI features
  - id, user_id, feature_type (script_generation/tts_generation), tokens_used, request_type, created_at
  - Enables plan-based usage limits and billing analytics

- **Generated Podcasts Table**: Complete podcast generation history
  - id, user_id, title, description, content, audio_url, voice_1, voice_2, duration_seconds, file_size_mb, tokens_used, status, error_message, created_at, updated_at
  - Tracks all podcast generations with detailed metadata

#### Legacy Tables (Maintained for Migration)
- **Podcast Model**: Original podcast table for backward compatibility

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

## API Requirements

### OpenAI API Access
- **Script Generation**: Uses GPT-4o for natural conversation generation
- **Audio Generation**: Uses OpenAI TTS-1 model with 6 voice options
- **Voice Options**: alloy, echo, fable, onyx, nova, shimmer
- **Cost**: Pay-per-use model, much more affordable than PlayHT

### Previous PlayHT Integration
- **Status**: Replaced with OpenAI TTS due to paid plan requirements
- **Voice Loading**: Previously worked with free plan (256 voices)
- **Audio Generation**: Required paid plan, now replaced with OpenAI

## Changelog

Changelog:
- July 05, 2025. Initial setup
- July 09, 2025. Updated PlayHT API integration to use v1 endpoints as per official documentation. Added dynamic voice loading with proper language grouping and search functionality. Enhanced voice selection UI with descriptions and language filtering.
- July 09, 2025. Added PostgreSQL database with proper environment variables. Database is now connected and ready for production use.
- July 09, 2025. Implemented complete PlayHT v1 API integration with dual-voice dialogue support using PlayDialog model. Added comprehensive error handling and proper job polling. Voice selection works with 256 real voices, but audio generation requires paid plan upgrade.
- July 09, 2025. **MAJOR UPDATE**: Replaced PlayHT with OpenAI TTS due to paid plan limitations. Implemented complete OpenAI TTS integration with dual-voice support, 6 voice options, and proper audio file handling. System now fully functional with structured Host 1:/Host 2: dialogue format.
- July 09, 2025. **DATABASE MIGRATION**: Created comprehensive Neon database schema with three main tables: Users (with Stripe integration and subscription plans), Usage (token tracking for AI features), and Generated Podcasts (complete podcast history). Added plan-based usage limits and subscription management capabilities.
- July 12, 2025. **PAYMENT SYSTEM OVERHAUL**: Replaced Stripe with Razorpay for Indian market. Added Google Pay integration with ID akkashyap479@oksbi. Updated pricing to INR currency. Fixed credit section display in header. Added comprehensive podcast management system with "Recent Podcasts" (3 most recent) and "All Podcasts" sections. Enhanced navigation with podcast management dropdown menu. Created payment checkout flow with Razorpay integration and Google Pay fallback option.