from app import db
from models import Usage, User
from datetime import datetime, timedelta
import logging

class UsageTracker:
    """Service for tracking token usage across AI features"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def track_usage(self, user_id, feature_type, tokens_used, request_type=None):
        """
        Track token usage for a user
        
        Args:
            user_id: ID of the user
            feature_type: Type of feature ('script_generation', 'tts_generation')
            tokens_used: Number of tokens consumed
            request_type: Specific API call type ('gpt-4o', 'tts-1', etc.)
        """
        try:
            # Get user and deduct credits
            user = User.query.get(user_id)
            if user:
                user.use_credits(tokens_used)
            
            usage_record = Usage(
                user_id=user_id,
                feature_type=feature_type,
                tokens_used=tokens_used,
                request_type=request_type
            )
            
            db.session.add(usage_record)
            db.session.commit()
            
            self.logger.info(f"Tracked usage: User {user_id}, {feature_type}, {tokens_used} tokens. Remaining credits: {user.credits if user else 'N/A'}")
            return True
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error tracking usage: {e}")
            return False
    
    def get_user_usage(self, user_id, days=30):
        """
        Get total token usage for a user over specified days
        
        Args:
            user_id: ID of the user
            days: Number of days to look back (default: 30)
            
        Returns:
            dict: Usage statistics
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            usage_records = Usage.query.filter(
                Usage.user_id == user_id,
                Usage.created_at >= cutoff_date
            ).all()
            
            total_tokens = sum(record.tokens_used for record in usage_records)
            
            # Group by feature type
            usage_by_feature = {}
            for record in usage_records:
                if record.feature_type not in usage_by_feature:
                    usage_by_feature[record.feature_type] = 0
                usage_by_feature[record.feature_type] += record.tokens_used
            
            return {
                'total_tokens': total_tokens,
                'usage_by_feature': usage_by_feature,
                'period_days': days,
                'total_requests': len(usage_records)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting user usage: {e}")
            return {
                'total_tokens': 0,
                'usage_by_feature': {},
                'period_days': days,
                'total_requests': 0
            }
    
    def check_usage_limits(self, user_id):
        """
        Check if user has exceeded their plan limits
        
        Args:
            user_id: ID of the user
            
        Returns:
            dict: Usage limit check results
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return {'error': 'User not found'}
            
            # Get plan limits
            plan_limits = user.get_plan_limits()
            
            # Get monthly usage
            monthly_usage = self.get_user_usage(user_id, days=30)
            
            # Check daily podcast count (last 24 hours)
            daily_cutoff = datetime.utcnow() - timedelta(hours=24)
            daily_podcasts = Usage.query.filter(
                Usage.user_id == user_id,
                Usage.feature_type == 'tts_generation',
                Usage.created_at >= daily_cutoff
            ).count()
            
            return {
                'plan_status': user.plan_status,
                'monthly_tokens_used': monthly_usage['total_tokens'],
                'monthly_tokens_limit': plan_limits['monthly_tokens'],
                'daily_podcasts_created': daily_podcasts,
                'daily_podcasts_limit': plan_limits['daily_podcasts'],
                'tokens_remaining': user.get_available_credits(),
                'podcasts_remaining': max(0, plan_limits['daily_podcasts'] - daily_podcasts),
                'can_generate_script': user.get_available_credits() > 0,
                'can_generate_audio': (user.get_available_credits() > 0 and 
                                     daily_podcasts < plan_limits['daily_podcasts']),
                'current_credits': user.credits,
                'total_credits_purchased': user.total_credits_purchased
            }
            
        except Exception as e:
            self.logger.error(f"Error checking usage limits: {e}")
            return {'error': 'Unable to check usage limits'}
    
    def get_usage_summary(self, user_id):
        """
        Get a comprehensive usage summary for dashboard display
        
        Args:
            user_id: ID of the user
            
        Returns:
            dict: Complete usage summary
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return {'error': 'User not found'}
            
            # Get usage statistics
            monthly_usage = self.get_user_usage(user_id, days=30)
            weekly_usage = self.get_user_usage(user_id, days=7)
            daily_usage = self.get_user_usage(user_id, days=1)
            
            # Get limit checks
            limit_status = self.check_usage_limits(user_id)
            
            return {
                'user': {
                    'username': user.username,
                    'plan_status': user.plan_status,
                    'plan_active': user.is_plan_active()
                },
                'usage': {
                    'monthly': monthly_usage,
                    'weekly': weekly_usage,
                    'daily': daily_usage
                },
                'limits': limit_status
            }
            
        except Exception as e:
            self.logger.error(f"Error getting usage summary: {e}")
            return {'error': 'Unable to get usage summary'}