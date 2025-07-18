from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import app, db
from models import User, Podcast, GeneratedPodcast, Usage
from playht_service import PlayHTService
from openai_service import OpenAIService
from usage_tracker import UsageTracker
from manual_payment_service import ManualPaymentService
import logging
import os

playht_service = PlayHTService()
openai_service = OpenAIService()
usage_tracker = UsageTracker()
payment_service = ManualPaymentService()

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
    # Get user's recent generated podcasts (new table) - only show recent 3
    user_podcasts = GeneratedPodcast.query.filter_by(user_id=current_user.id).order_by(GeneratedPodcast.created_at.desc()).limit(3).all()
    
    # Get usage statistics
    usage_stats = usage_tracker.check_usage_limits(current_user.id)
    
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
    
    return render_template('generator_openai.html', podcasts=user_podcasts, usage_stats=usage_stats)

@app.route('/generate-podcast', methods=['POST'])
@login_required
def generate_podcast():
    title = request.form.get('title')
    description = request.form.get('description')
    content = request.form.get('content')
    voice1 = request.form.get('voice1')
    voice2 = request.form.get('voice2')
    
    if not all([title, description, content, voice1, voice2]):
        flash('Title, description, script content, and both voice selections are required.', 'error')
        return redirect(url_for('generator'))
    
    # Check usage limits before processing
    usage_limits = usage_tracker.check_usage_limits(current_user.id)
    if usage_limits.get('error'):
        flash('Unable to verify usage limits. Please try again.', 'error')
        return redirect(url_for('generator'))
    
    if not usage_limits.get('can_generate_audio'):
        if usage_limits.get('podcasts_remaining', 0) <= 0:
            flash(f'Daily podcast limit reached ({usage_limits.get("daily_podcasts_limit", 0)}). Upgrade your plan for more podcasts.', 'warning')
        else:
            flash(f'Monthly token limit reached ({usage_limits.get("monthly_tokens_limit", 0)}). Upgrade your plan for more tokens.', 'warning')
        return redirect(url_for('pricing'))
    
    try:
        # Use the provided script content directly (user formats it with Host 1:/Host 2:)
        logging.info(f"Processing podcast script for: {title}")
        
        # Use selected OpenAI voices
        host1_voice = voice1 if voice1 in ['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer'] else 'alloy'
        host2_voice = voice2 if voice2 in ['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer'] else 'echo'
        
        # Create new GeneratedPodcast record
        generated_podcast = GeneratedPodcast(
            title=title,
            description=description,
            content=content,  # Store original content with Host 1/Host 2 labels
            user_id=current_user.id,
            voice_1=host1_voice,
            voice_2=host2_voice,
            status='processing'
        )
        
        db.session.add(generated_podcast)
        db.session.commit()
        
        # Generate audio using OpenAI TTS with dual voices
        logging.info(f"Generating audio with OpenAI TTS")
        
        if openai_service.client:
            audio_result = openai_service.generate_dual_voice_audio(
                script_content=content,
                host1_voice=host1_voice,
                host2_voice=host2_voice
            )
            
            if audio_result.get('success'):
                # Save audio file to static directory
                import shutil
                import os
                import time
                audio_filename = f"podcast_{generated_podcast.id}_{int(time.time())}.mp3"
                audio_path = os.path.join('static', 'audio', audio_filename)
                
                # Create audio directory if it doesn't exist
                os.makedirs(os.path.dirname(audio_path), exist_ok=True)
                
                # Move temp file to static directory
                shutil.move(audio_result['audio_file'], audio_path)
                
                # Update podcast record with audio info
                generated_podcast.audio_url = f'/static/audio/{audio_filename}'
                generated_podcast.duration_seconds = int(audio_result.get('duration', 0))
                generated_podcast.file_size_mb = audio_result.get('file_size_mb', 0)
                generated_podcast.tokens_used = audio_result.get('tokens_used', 0)
                generated_podcast.status = 'completed'
                
                # Track TTS usage
                usage_tracker.track_usage(
                    user_id=current_user.id,
                    feature_type='tts_generation',
                    tokens_used=audio_result.get('tokens_used', 0),
                    request_type='tts-1'
                )
                
                flash(f'Podcast "{title}" generated successfully using OpenAI TTS!', 'success')
            else:
                generated_podcast.status = 'failed'
                generated_podcast.error_message = audio_result.get('error', 'Unknown error')
                error_message = audio_result.get('error', 'Unknown error')
                flash(f'Failed to generate audio: {error_message}. Your script has been saved and you can retry later.', 'warning')
        else:
            # OpenAI not available - save as text-only
            generated_podcast.status = 'completed'
            flash(f'Podcast "{title}" saved as text! Audio generation requires OpenAI API key.', 'info')
        
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error generating podcast: {e}")
        flash('An error occurred while generating the podcast.', 'error')
    
    return redirect(url_for('generator'))

@app.route('/podcast/<int:podcast_id>')
@login_required
def view_podcast(podcast_id):
    # Try to get from GeneratedPodcast table first (new format)
    podcast = GeneratedPodcast.query.filter_by(id=podcast_id, user_id=current_user.id).first()
    
    # If not found, try legacy Podcast table
    if not podcast:
        podcast = Podcast.query.filter_by(id=podcast_id, user_id=current_user.id).first_or_404()
    
    return render_template('podcast_detail.html', podcast=podcast)

@app.route('/delete-podcast/<int:podcast_id>', methods=['POST'])
@login_required
def delete_podcast(podcast_id):
    # Try to get from GeneratedPodcast table first (new format)
    podcast = GeneratedPodcast.query.filter_by(id=podcast_id, user_id=current_user.id).first()
    
    # If not found, try legacy Podcast table
    if not podcast:
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

# Payment Routes
@app.route('/pricing')
@login_required
def pricing():
    """Display pricing plans"""
    plans = payment_service.get_all_plans()
    token_packages = payment_service.get_token_packages()
    payment_instructions = payment_service.get_payment_instructions()
    usage_stats = usage_tracker.check_usage_limits(current_user.id)
    
    return render_template('pricing.html', 
                         plans=plans, 
                         token_packages=token_packages,
                         payment_instructions=payment_instructions,
                         usage_stats=usage_stats, 
                         current_plan=current_user.plan_status)

@app.route('/upgrade/<plan_type>')
@login_required
def upgrade_plan(plan_type):
    """Show payment details for plan upgrade"""
    if plan_type == 'free':
        flash('You are already on the free plan.', 'info')
        return redirect(url_for('pricing'))
    
    payment_details = payment_service.get_payment_details(plan_type=plan_type)
    if not payment_details:
        flash('Invalid plan selected.', 'error')
        return redirect(url_for('pricing'))
    
    # Generate UPI URL for the payment
    upi_url = payment_service.generate_upi_payment_url(
        payment_details['amount'], 
        payment_details['payment_note']
    )
    payment_details['upi_url'] = upi_url
    
    return render_template('manual_payment.html', 
                         payment_details=payment_details,
                         current_user=current_user)

@app.route('/buy-tokens/<int:token_amount>')
@login_required
def buy_tokens(token_amount):
    """Show payment details for token purchase"""
    valid_amounts = [10000, 25000, 50000, 100000]
    if token_amount not in valid_amounts:
        flash('Invalid token amount selected.', 'error')
        return redirect(url_for('pricing'))
    
    payment_details = payment_service.get_payment_details(token_amount=token_amount)
    if not payment_details:
        flash('Invalid token amount selected.', 'error')
        return redirect(url_for('pricing'))
    
    # Generate UPI URL for the payment
    upi_url = payment_service.generate_upi_payment_url(
        payment_details['amount'], 
        payment_details['payment_note']
    )
    payment_details['upi_url'] = upi_url
    
    return render_template('manual_payment.html', 
                         payment_details=payment_details,
                         current_user=current_user)

@app.route('/payment/confirm', methods=['POST'])
@login_required
def confirm_payment():
    """Handle manual payment confirmation"""
    transaction_id = request.form.get('transaction_id')
    payment_type = request.form.get('payment_type')
    plan_type = request.form.get('plan_type')
    token_amount = request.form.get('token_amount')
    
    if not transaction_id:
        flash('Please provide transaction ID.', 'error')
        return redirect(url_for('pricing'))
    
    if payment_type == 'plan' and plan_type:
        # Automatically upgrade user plan and add credits
        result = payment_service.upgrade_user_plan(current_user.id, plan_type, transaction_id)
        if result.get('success'):
            flash(f'Payment successful! Upgraded to {result["plan_name"]} plan. Added {result["credits_added"]:,} credits. Total credits: {result["total_credits"]:,}', 'success')
        else:
            flash(f'Payment received! Your request to upgrade to {plan_type} plan has been submitted. Transaction ID: {transaction_id}. Your account will be upgraded within 24 hours.', 'success')
    elif payment_type == 'tokens' and token_amount:
        # Automatically add credits to user account
        result = payment_service.add_tokens_to_user(current_user.id, int(token_amount), transaction_id)
        if result.get('success'):
            flash(f'Payment successful! Added {result["credits_added"]:,} credits. Total credits: {result["total_credits"]:,}', 'success')
        else:
            flash(f'Payment received! Your request to purchase {token_amount} tokens has been submitted. Transaction ID: {transaction_id}. Tokens will be added within 24 hours.', 'success')
    else:
        flash('Invalid payment details.', 'error')
        return redirect(url_for('pricing'))
    
    return redirect(url_for('generator'))

# Admin routes for manual payment processing
@app.route('/admin/upgrade-user', methods=['POST'])
@login_required
def admin_upgrade_user():
    """Admin route to manually upgrade user plan"""
    # This would typically have admin authentication
    # For now, it's a simple route for manual processing
    user_id = request.form.get('user_id')
    plan_type = request.form.get('plan_type')
    transaction_id = request.form.get('transaction_id')
    
    if not all([user_id, plan_type]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    result = payment_service.upgrade_user_plan(user_id, plan_type, transaction_id)
    
    if result.get('success'):
        return jsonify({'message': f'User {user_id} upgraded to {plan_type} successfully'})
    else:
        return jsonify({'error': result.get('error', 'Unknown error')}), 500

@app.route('/payment/cancel')
@login_required
def payment_cancel():
    """Handle cancelled payment"""
    flash('Payment was cancelled.', 'info')
    return redirect(url_for('pricing'))

# Podcast Management Routes
@app.route('/my-podcasts')
@login_required
def my_podcasts():
    """Display all user's podcasts"""
    # Get all podcasts from GeneratedPodcast table
    podcasts = GeneratedPodcast.query.filter_by(user_id=current_user.id).order_by(GeneratedPodcast.created_at.desc()).all()
    
    # Also get legacy podcasts from Podcast table
    legacy_podcasts = Podcast.query.filter_by(user_id=current_user.id).order_by(Podcast.created_at.desc()).all()
    
    return render_template('my_podcasts.html', podcasts=podcasts, legacy_podcasts=legacy_podcasts)

@app.route('/recent-podcasts')
@login_required
def recent_podcasts():
    """Display recent 3 podcasts"""
    # Get recent 3 podcasts from GeneratedPodcast table
    recent_podcasts = GeneratedPodcast.query.filter_by(user_id=current_user.id).order_by(GeneratedPodcast.created_at.desc()).limit(3).all()
    
    return render_template('recent_podcasts.html', podcasts=recent_podcasts)

@app.route('/usage-stats')
@login_required
def usage_stats():
    """Display user usage statistics and limits"""
    stats = usage_tracker.get_usage_summary(current_user.id)
    return render_template('usage_stats.html', stats=stats)

@app.route('/api/usage')
@login_required
def get_usage_api():
    """API endpoint to get user usage statistics"""
    try:
        stats = usage_tracker.check_usage_limits(current_user.id)
        return jsonify(stats)
    except Exception as e:
        logging.error(f"Error getting usage stats: {e}")
        return jsonify({
            'error': 'Unable to load usage stats',
            'tokens_remaining': 0,
            'monthly_tokens_limit': 5000,
            'plan_status': current_user.plan_status
        })

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
