import os
import razorpay
import logging
from datetime import datetime, timedelta
from app import db
from models import User

class RazorpayService:
    """Service for handling Razorpay payments and subscriptions"""
    
    def __init__(self):
        self.razorpay_key_id = os.environ.get("RAZORPAY_KEY_ID")
        self.razorpay_key_secret = os.environ.get("RAZORPAY_KEY_SECRET")
        
        if self.razorpay_key_id and self.razorpay_key_secret:
            self.client = razorpay.Client(auth=(self.razorpay_key_id, self.razorpay_key_secret))
        else:
            self.client = None
            logging.warning("Razorpay credentials not found in environment variables")
        
        self.logger = logging.getLogger(__name__)
        
        # Plan configurations (prices in INR)
        self.plans = {
            'free': {
                'name': 'Free Plan',
                'price': 0,
                'monthly_tokens': 10000,
                'daily_podcasts': 3,
                'description': 'Perfect for getting started with AI podcasts'
            },
            'pro': {
                'name': 'Pro Plan',
                'price': 249,  # INR
                'monthly_tokens': 100000,
                'daily_podcasts': 20,
                'description': 'Great for regular podcast creators'
            },
            'elite': {
                'name': 'Elite Plan',
                'price': 499,  # INR
                'monthly_tokens': 500000,
                'daily_podcasts': 100,
                'description': 'For professional podcast producers'
            }
        }
        
        # Google Pay Information
        self.google_pay_id = "akkashyap479@oksbi"
    
    def create_order(self, user_id, plan_type):
        """Create a Razorpay order for plan upgrade"""
        try:
            if not self.client:
                return {'error': 'Payment service unavailable'}
            
            user = User.query.get(user_id)
            if not user:
                return {'error': 'User not found'}
            
            plan = self.plans.get(plan_type)
            if not plan or plan_type == 'free':
                return {'error': 'Invalid plan selected'}
            
            # Create order
            order_data = {
                "amount": plan['price'] * 100,  # Amount in paise
                "currency": "INR",
                "receipt": f"order_{user_id}_{plan_type}_{int(datetime.now().timestamp())}",
                "payment_capture": 1
            }
            
            order = self.client.order.create(data=order_data)
            
            return {
                'order_id': order['id'],
                'amount': order['amount'],
                'currency': order['currency'],
                'plan_name': plan['name'],
                'plan_type': plan_type,
                'user_id': user_id
            }
            
        except Exception as e:
            self.logger.error(f"Error creating Razorpay order: {e}")
            return {'error': 'Failed to create payment order'}
    
    def verify_payment(self, payment_id, order_id, signature):
        """Verify Razorpay payment signature"""
        try:
            if not self.client:
                return False
            
            params_dict = {
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }
            
            self.client.utility.verify_payment_signature(params_dict)
            return True
            
        except Exception as e:
            self.logger.error(f"Payment verification failed: {e}")
            return False
    
    def handle_successful_payment(self, payment_id, order_id, user_id, plan_type):
        """Handle successful payment completion"""
        try:
            # Update user's plan
            user = User.query.get(user_id)
            if user:
                user.plan_status = plan_type
                user.expires_at = datetime.utcnow() + timedelta(days=30)
                db.session.commit()
                
                self.logger.info(f"Updated user {user_id} to {plan_type} plan")
                
                return {
                    'success': True,
                    'plan': plan_type,
                    'expires_at': user.expires_at
                }
            
            return {'error': 'User not found'}
            
        except Exception as e:
            self.logger.error(f"Error handling payment: {e}")
            return {'error': 'Failed to process payment'}
    
    def create_token_order(self, user_id, token_amount):
        """Create Razorpay order for additional token purchases"""
        try:
            if not self.client:
                return {'error': 'Payment service unavailable'}
            
            user = User.query.get(user_id)
            if not user:
                return {'error': 'User not found'}
            
            # Token packages (prices in INR)
            token_packages = {
                10000: {'price': 79, 'name': '10,000 Tokens'},
                25000: {'price': 159, 'name': '25,000 Tokens'},
                50000: {'price': 279, 'name': '50,000 Tokens'},
                100000: {'price': 499, 'name': '100,000 Tokens'}
            }
            
            package = token_packages.get(token_amount)
            if not package:
                return {'error': 'Invalid token package'}
            
            order_data = {
                "amount": package['price'] * 100,  # Amount in paise
                "currency": "INR",
                "receipt": f"tokens_{user_id}_{token_amount}_{int(datetime.now().timestamp())}",
                "payment_capture": 1
            }
            
            order = self.client.order.create(data=order_data)
            
            return {
                'order_id': order['id'],
                'amount': order['amount'],
                'currency': order['currency'],
                'package_name': package['name'],
                'token_amount': token_amount,
                'user_id': user_id
            }
            
        except Exception as e:
            self.logger.error(f"Error creating token order: {e}")
            return {'error': 'Failed to create payment order'}
    
    def handle_token_purchase(self, payment_id, order_id, user_id, token_amount):
        """Handle successful token purchase"""
        try:
            user = User.query.get(user_id)
            if user:
                # Extend user's plan or upgrade to Pro
                if user.expires_at and user.expires_at > datetime.utcnow():
                    days_to_add = max(7, token_amount // 10000)
                    user.expires_at += timedelta(days=days_to_add)
                else:
                    user.plan_status = 'pro'
                    user.expires_at = datetime.utcnow() + timedelta(days=30)
                
                db.session.commit()
                
                self.logger.info(f"Added {token_amount} tokens to user {user_id}")
                
                return {
                    'success': True,
                    'tokens_added': token_amount,
                    'new_expires_at': user.expires_at
                }
            
            return {'error': 'User not found'}
            
        except Exception as e:
            self.logger.error(f"Error handling token purchase: {e}")
            return {'error': 'Failed to process token purchase'}
    
    def get_plan_info(self, plan_type):
        """Get plan information"""
        return self.plans.get(plan_type, self.plans['free'])
    
    def get_all_plans(self):
        """Get all available plans"""
        return self.plans
    
    def get_google_pay_id(self):
        """Get Google Pay ID for manual payments"""
        return self.google_pay_id