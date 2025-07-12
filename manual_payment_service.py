"""
Manual Payment Service for UPI-based payments
"""
import logging
from datetime import datetime, timedelta
from app import db
from models import User

class ManualPaymentService:
    """Service for handling manual UPI payments"""
    
    def __init__(self):
        self.upi_id = "akkashyap479@oksbi"
        self.merchant_name = "Abhishek Kashyap"
        
    def get_all_plans(self):
        """Get all available plans with INR pricing"""
        return {
            'free': {
                'name': 'Free',
                'price': 0,
                'monthly_tokens': 5000,
                'daily_podcasts': 3,
                'description': 'Perfect for getting started with AI podcasts'
            },
            'pro': {
                'name': 'Pro',
                'price': 2,
                'monthly_tokens': 50000,
                'daily_podcasts': 25,
                'description': 'Great for regular podcast creators'
            },
            'elite': {
                'name': 'Elite',
                'price': 499,
                'monthly_tokens': 150000,
                'daily_podcasts': 100,
                'description': 'For professional podcast producers'
            }
        }
    
    def get_token_packages(self):
        """Get available token packages"""
        return [
            {'tokens': 10000, 'price': 79, 'popular': False},
            {'tokens': 25000, 'price': 159, 'popular': True},
            {'tokens': 50000, 'price': 279, 'popular': False},
            {'tokens': 100000, 'price': 499, 'popular': False}
        ]
    
    def get_plan_info(self, plan_type):
        """Get plan information"""
        plans = self.get_all_plans()
        return plans.get(plan_type, plans['free'])
    
    def get_payment_details(self, plan_type=None, token_amount=None):
        """Get payment details for manual payment"""
        if plan_type:
            plan = self.get_plan_info(plan_type)
            return {
                'type': 'plan',
                'plan_type': plan_type,
                'plan_name': plan['name'],
                'amount': plan['price'],
                'description': f'Upgrade to {plan["name"]} Plan',
                'upi_id': self.upi_id,
                'merchant_name': self.merchant_name,
                'qr_code_path': '/static/images/payment-qr.jpg',
                'payment_note': f'AI Podcast {plan["name"]} - {self.merchant_name}'
            }
        elif token_amount:
            packages = self.get_token_packages()
            package = next((p for p in packages if p['tokens'] == token_amount), None)
            if package:
                return {
                    'type': 'tokens',
                    'token_amount': token_amount,
                    'amount': package['price'],
                    'description': f'Purchase {token_amount:,} tokens',
                    'upi_id': self.upi_id,
                    'merchant_name': self.merchant_name,
                    'qr_code_path': '/static/images/payment-qr.jpg',
                    'payment_note': f'AI Podcast Tokens - {self.merchant_name}'
                }
        return None
    
    def generate_upi_payment_url(self, amount, note="AI Podcast Payment"):
        """Generate UPI payment URL for QR code with fixed amount"""
        # UPI payment URL format: upi://pay?pa=UPI_ID&pn=NAME&am=AMOUNT&cu=INR&tn=NOTE
        upi_url = f"upi://pay?pa={self.upi_id}&pn={self.merchant_name}&am={amount}&cu=INR&tn={note}"
        return upi_url
    
    def upgrade_user_plan(self, user_id, plan_type, transaction_id=None):
        """Manually upgrade user plan (admin function)"""
        try:
            user = User.query.get(user_id)
            if not user:
                return {'error': 'User not found'}
            
            plan_info = self.get_plan_info(plan_type)
            
            # Update user plan
            user.plan_status = plan_type
            user.expires_at = datetime.utcnow() + timedelta(days=30)
            
            # Add credits based on plan
            credits_to_add = plan_info['monthly_tokens']
            user.add_credits(credits_to_add)
            
            db.session.commit()
            
            logging.info(f"User {user_id} upgraded to {plan_type} plan and received {credits_to_add} credits")
            
            return {
                'success': True,
                'plan': plan_type,
                'plan_name': plan_info['name'],
                'expires_at': user.expires_at,
                'credits_added': credits_to_add,
                'total_credits': user.credits
            }
            
        except Exception as e:
            logging.error(f"Error upgrading user plan: {e}")
            db.session.rollback()
            return {'error': str(e)}
    
    def add_tokens_to_user(self, user_id, token_amount, transaction_id=None):
        """Manually add tokens to user (admin function)"""
        try:
            user = User.query.get(user_id)
            if not user:
                return {'error': 'User not found'}
            
            # Add credits to user account
            user.add_credits(token_amount)
            
            db.session.commit()
            
            logging.info(f"Added {token_amount} credits to user {user_id}")
            
            return {
                'success': True,
                'credits_added': token_amount,
                'total_credits': user.credits
            }
            
        except Exception as e:
            logging.error(f"Error adding credits: {e}")
            db.session.rollback()
            return {'error': str(e)}
    
    def get_upi_id(self):
        """Get UPI ID for payments"""
        return self.upi_id
    
    def get_payment_instructions(self):
        """Get payment instructions for users"""
        return {
            'upi_id': self.upi_id,
            'merchant_name': self.merchant_name,
            'instructions': [
                f"Send payment to UPI ID: {self.upi_id}",
                "Or scan the QR code with any UPI app",
                "Include your username in the payment description",
                "Contact support with transaction ID after payment",
                "Your account will be upgraded within 24 hours"
            ]
        }