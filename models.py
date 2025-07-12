from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    razorpay_customer_id = db.Column(db.String(255), unique=True)
    plan_status = db.Column(db.String(20), default='free')  # free, pro, elite
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    usage_records = db.relationship('Usage', backref='user', lazy=True, cascade='all, delete-orphan')
    generated_podcasts = db.relationship('GeneratedPodcast', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_plan_active(self):
        """Check if user's plan is currently active"""
        if self.plan_status == 'free':
            return True
        if self.expires_at and self.expires_at > datetime.utcnow():
            return True
        return False
    
    def get_plan_limits(self):
        """Get usage limits based on plan status"""
        limits = {
            'free': {'monthly_tokens': 10000, 'daily_podcasts': 3},
            'pro': {'monthly_tokens': 100000, 'daily_podcasts': 20},
            'elite': {'monthly_tokens': 500000, 'daily_podcasts': 100}
        }
        return limits.get(self.plan_status, limits['free'])
    
    def __repr__(self):
        return f'<User {self.username}>'

class Usage(db.Model):
    __tablename__ = 'usage'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    feature_type = db.Column(db.String(50), nullable=False)  # 'script_generation', 'tts_generation'
    tokens_used = db.Column(db.Integer, nullable=False)
    request_type = db.Column(db.String(100))  # 'gpt-4', 'tts-1', etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Usage {self.user_id}:{self.feature_type}:{self.tokens_used}>'

class GeneratedPodcast(db.Model):
    __tablename__ = 'generated_podcasts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    content = db.Column(db.Text, nullable=False)
    audio_url = db.Column(db.String(500))
    voice_1 = db.Column(db.String(50))  # OpenAI voice used for Host 1
    voice_2 = db.Column(db.String(50))  # OpenAI voice used for Host 2
    duration_seconds = db.Column(db.Integer)
    file_size_mb = db.Column(db.Float)
    tokens_used = db.Column(db.Integer)
    status = db.Column(db.String(50), default='pending')  # pending, processing, completed, failed
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<GeneratedPodcast {self.title}>'

# Legacy model - keeping for backward compatibility during migration
class Podcast(db.Model):
    __tablename__ = 'podcast'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    content = db.Column(db.Text, nullable=False)
    audio_url = db.Column(db.String(500))
    playht_job_id = db.Column(db.String(100))
    status = db.Column(db.String(50), default='pending')  # pending, processing, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    def __repr__(self):
        return f'<Podcast {self.title}>'
