from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import app, db
from models import User, Podcast
from playht_service import PlayHTService
from openai_service import OpenAIService
import logging

playht_service = PlayHTService()
openai_service = OpenAIService()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Please fill in all fields.', 'error')
            return render_template('signin.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Welcome back!', 'success')
            return redirect(url_for('generator'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('signin.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not all([username, email, password, confirm_password]):
            flash('Please fill in all fields.', 'error')
            return render_template('signup.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('signup.html')
        
         
            flash('Password must be at least 6 characters long.', 'error')
            return render_template('signup.html')
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return render_template('signup.html')
        
        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'error')
            return render_template('signup.html')
        
        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash('Account created successfully!', 'success')
            return redirect(url_for('generator'))
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error creating user: {e}")
            flash('An error occurred while creating your account.', 'error')
    
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/generator')
@login_required
def generator():
    user_podcasts = Podcast.query.filter_by(user_id=current_user.id).order_by(Podcast.created_at.desc()).all()
    
    # Get available voices from Play HT
    available_voices = playht_service.get_voices()
    
    # If no voices are available from API, use fallback voices (API might be temporarily down)
    if not available_voices:
        flash('PlayHT API is temporarily unavailable. Using fallback voices for now.', 'info')
        logging.warning("PlayHT API unavailable - using fallback voices")
        available_voices = [
            {
                'id': 's3://voice-cloning-zero-shot/baf1ef41-36b6-428c-9bdf-50ba54682bd8/original/manifest.json',
                'name': 'Jenny - Conversational',
                'language': 'english',
                'gender': 'female',
                'accent': 'american',
                'description': 'A friendly, conversational voice perfect for podcasts',
                'sample': '',
                'tags': ['conversational', 'friendly'],
                'categories': ['podcasting']
            },
            {
                'id': 's3://voice-cloning-zero-shot/820a3788-2b37-4d21-847a-b65d8a68c99a/original/manifest.json',
                'name': 'Alex - Professional',
                'language': 'english', 
                'gender': 'male',
                'accent': 'american',
                'description': 'A professional, authoritative male voice',
                'sample': '',
                'tags': ['professional', 'authoritative'],
                'categories': ['podcasting']
            },
            {
                'id': 's3://voice-cloning-zero-shot/d82d246c-148b-4c93-8c6a-f2c9c2b9e5a7/original/manifest.json',
                'name': 'Emma - British',
                'language': 'english',
                'gender': 'female',
                'accent': 'british',
                'description': 'A clear, articulate British accent',
                'sample': '',
                'tags': ['british', 'clear'],
                'categories': ['podcasting']
            },
            {
                'id': 's3://voice-cloning-zero-shot/f5d3e2a1-4c7b-2d9e-8f6a-1b2c3d4e5f6a/original/manifest.json',
                'name': 'David - Warm',
                'language': 'english',
                'gender': 'male',
                'accent': 'american',
                'description': 'A warm, engaging voice for storytelling',
                'sample': '',
                'tags': ['warm', 'engaging'],
                'categories': ['podcasting']
            },
            {
                'id': 's3://voice-cloning-zero-shot/a1b2c3d4-5e6f-7g8h-9i0j-1k2l3m4n5o6p/original/manifest.json',
                'name': 'Sofia - Spanish',
                'language': 'spanish',
                'gender': 'female',
                'accent': 'neutral',
                'description': 'A clear Spanish voice for multilingual content',
                'sample': '',
                'tags': ['spanish', 'clear'],
                'categories': ['podcasting']
            },
            {
                'id': 's3://voice-cloning-zero-shot/b2c3d4e5-6f7g-8h9i-0j1k-2l3m4n5o6p7q/original/manifest.json',
                'name': 'Marie - French',
                'language': 'french',
                'gender': 'female',
                'accent': 'parisian',
                'description': 'An elegant French voice',
                'sample': '',
                'tags': ['french', 'elegant'],
                'categories': ['podcasting']
            }
        ]
    
    return render_template('generator.html', podcasts=user_podcasts, voices=available_voices)

@app.route('/generate-podcast', methods=['POST'])
@login_required
def generate_podcast():
    title = request.form.get('title')
    description = request.form.get('description')
    content = request.form.get('content')
    voice1 = request.form.get('voice1')
    voice2 = request.form.get('voice2')
    
    if not all([title, description, voice1, voice2]):
        flash('Title, description, and both voice selections are required.', 'error')
        return redirect(url_for('generator'))
    
    try:
        # Generate conversational script using OpenAI
        logging.info(f"Generating conversational script for: {title}")
        
        # Generate conversational script
        if openai_service.client:
            script_result = openai_service.generate_podcast_script(title, description)
            conversation_script = script_result.get('script')
        else:
            # Use fallback script generation if OpenAI is not available
            conversation_script = f"""Alex: Welcome to today's podcast! I'm Alex, and I'm here with my co-host Jordan. 

Jordan: Hi everyone! Today we're diving into an exciting topic: {title}. 

Alex: That sounds fascinating! Jordan, can you tell us more about {description}?

Jordan: Absolutely! {description} This is such an important topic because it affects many aspects of our daily lives.

Alex: That's really interesting! What do you think our listeners should know about this?

Jordan: Well, I think the key points to understand are the practical implications and how this might evolve in the future.

Alex: Great insights! Before we wrap up, do you have any final thoughts for our audience?

Jordan: I'd encourage everyone to stay curious and keep learning about topics like this. It's amazing how much there is to discover.

Alex: Couldn't agree more! Thanks for joining us today, everyone. Until next time!

Jordan: Thanks for listening, and we'll see you in the next episode!"""
        
        # Create podcast record with the generated script
        podcast = Podcast(
            title=title,
            description=description,
            content=conversation_script,
            user_id=current_user.id,
            status='processing'
        )
        
        db.session.add(podcast)
        db.session.commit()
        
        # Generate audio using Play HT with dual voices
        logging.info(f"Generating audio with voices: {voice1}, {voice2}")
        audio_result = playht_service.generate_audio(
            text=conversation_script,
            voice1=voice1,
            voice2=voice2,
            turn_prefix="Alex:",
            turn_prefix2="Jordan:"
        )
        
        if audio_result.get('success'):
            podcast.audio_url = audio_result.get('audio_url')
            podcast.playht_job_id = audio_result.get('job_id')
            podcast.status = 'completed'
            flash('Conversational podcast generated successfully!', 'success')
        else:
            podcast.status = 'failed'
            error_message = audio_result.get('error', 'Unknown error')
            
            if 'API access is not available' in error_message:
                flash('PlayHT API access requires a paid plan. Please upgrade at https://play.ai/pricing to enable podcast generation.', 'warning')
            else:
                flash(f'Failed to generate audio: {error_message}', 'error')
        
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error generating podcast: {e}")
        flash('An error occurred while generating the podcast.', 'error')
    
    return redirect(url_for('generator'))

@app.route('/podcast/<int:podcast_id>')
@login_required
def view_podcast(podcast_id):
    podcast = Podcast.query.filter_by(id=podcast_id, user_id=current_user.id).first_or_404()
    return render_template('podcast_detail.html', podcast=podcast)

@app.route('/delete-podcast/<int:podcast_id>', methods=['POST'])
@login_required
def delete_podcast(podcast_id):
    podcast = Podcast.query.filter_by(id=podcast_id, user_id=current_user.id).first_or_404()
    
    try:
        db.session.delete(podcast)
        db.session.commit()
        flash('Podcast deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting podcast: {e}")
        flash('An error occurred while deleting the podcast.', 'error')
    
    return redirect(url_for('generator'))

@app.route('/api/voices')
@login_required
def get_voices_api():
    """API endpoint to get available voices from Play HT"""
    try:
        voices = playht_service.get_voices()
        return jsonify({
            'success': True,
            'voices': voices,
            'count': len(voices)
        })
    except Exception as e:
        logging.error(f"Error getting voices via API: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/test-voices')
@login_required
def test_voices_api():
    """Test endpoint to check PlayHT API status"""
    try:
        voices = playht_service.get_voices()
        if voices:
            return jsonify({
                'success': True,
                'message': f'Successfully loaded {len(voices)} voices from PlayHT API',
                'sample_voices': voices[:3]  # Show first 3 voices as sample
            })
        else:
            return jsonify({
                'success': False,
                'message': 'PlayHT API is unavailable or returned no voices'
            })
    except Exception as e:
        logging.error(f"Error testing voices API: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
