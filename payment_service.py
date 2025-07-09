import os
import stripe
import logging
from datetime import datetime, timedelta
from app import db
from models import User

class PaymentService:
    """Service for handling Stripe payments and subscriptions"""
    
    def __init__(self):
        self.stripe_secret_key = os.environ.get("STRIPE_SECRET_KEY")
        self.stripe_publishable_key = os.environ.get("STRIPE_PUBLISHABLE_KEY")
        
        if self.stripe_secret_key:
            stripe.api_key = self.stripe_secret_key
        else:
            logging.warning("Stripe secret key not found in environment variables")
        
        self.logger = logging.getLogger(__name__)
        
        # Plan configurations
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
                'price': 3.00,
                'monthly_tokens': 100000,
                'daily_podcasts': 20,
                'description': 'Great for regular podcast creators'
            },
            'elite': {
                'name': 'Elite Plan',
                'price': 5.00,
                'monthly_tokens': 500000,
                'daily_podcasts': 100,
                'description': 'For professional podcast producers'
            }
        }
    
    def create_customer(self, user_id, email, name):
        """Create a Stripe customer for the user"""
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={'user_id': user_id}
            )
            
            # Update user with Stripe customer ID
            user = User.query.get(user_id)
            if user:
                user.stripe_customer_id = customer.id
                db.session.commit()
                self.logger.info(f"Created Stripe customer for user {user_id}")
            
            return customer
            
        except stripe.error.StripeError as e:
            self.logger.error(f"Stripe error creating customer: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error creating customer: {e}")
            return None
    
    def create_checkout_session(self, user_id, plan_type):
        """Create a Stripe Checkout session for plan upgrade"""
        try:
            user = User.query.get(user_id)
            if not user:
                return {'error': 'User not found'}
            
            plan = self.plans.get(plan_type)
            if not plan or plan_type == 'free':
                return {'error': 'Invalid plan selected'}
            
            # Create Stripe customer if not exists
            if not user.stripe_customer_id:
                customer = self.create_customer(user_id, user.email, user.username)
                if not customer:
                    return {'error': 'Failed to create customer'}
            
            # Calculate expiration date (30 days from now)
            expires_at = datetime.utcnow() + timedelta(days=30)
            
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                customer=user.stripe_customer_id,
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': plan['name'],
                            'description': plan['description']
                        },
                        'unit_amount': int(plan['price'] * 100),  # Convert to cents
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=f"{os.environ.get('REPLIT_DOMAIN', 'http://localhost:5000')}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{os.environ.get('REPLIT_DOMAIN', 'http://localhost:5000')}/payment/cancel",
                metadata={
                    'user_id': user_id,
                    'plan_type': plan_type,
                    'expires_at': expires_at.isoformat()
                }
            )
            
            return {
                'session_id': session.id,
                'checkout_url': session.url
            }
            
        except stripe.error.StripeError as e:
            self.logger.error(f"Stripe error creating checkout session: {e}")
            return {'error': f'Payment error: {str(e)}'}
        except Exception as e:
            self.logger.error(f"Error creating checkout session: {e}")
            return {'error': 'Failed to create payment session'}
    
    def handle_successful_payment(self, session_id):
        """Handle successful payment completion"""
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            
            if session.payment_status == 'paid':
                user_id = int(session.metadata.get('user_id'))
                plan_type = session.metadata.get('plan_type')
                expires_at = datetime.fromisoformat(session.metadata.get('expires_at'))
                
                # Update user's plan
                user = User.query.get(user_id)
                if user:
                    user.plan_status = plan_type
                    user.expires_at = expires_at
                    db.session.commit()
                    
                    self.logger.info(f"Updated user {user_id} to {plan_type} plan")
                    
                    return {
                        'success': True,
                        'plan': plan_type,
                        'expires_at': expires_at
                    }
            
            return {'error': 'Payment not completed'}
            
        except stripe.error.StripeError as e:
            self.logger.error(f"Stripe error handling payment: {e}")
            return {'error': f'Payment verification failed: {str(e)}'}
        except Exception as e:
            self.logger.error(f"Error handling payment: {e}")
            return {'error': 'Failed to process payment'}
    
    def create_token_purchase_session(self, user_id, token_amount):
        """Create checkout session for additional token purchases"""
        try:
            user = User.query.get(user_id)
            if not user:
                return {'error': 'User not found'}
            
            # Token packages
            token_packages = {
                10000: {'price': 1.00, 'name': '10,000 Tokens'},
                25000: {'price': 2.00, 'name': '25,000 Tokens'},
                50000: {'price': 3.50, 'name': '50,000 Tokens'},
                100000: {'price': 6.00, 'name': '100,000 Tokens'}
            }
            
            package = token_packages.get(token_amount)
            if not package:
                return {'error': 'Invalid token package'}
            
            # Create Stripe customer if not exists
            if not user.stripe_customer_id:
                customer = self.create_customer(user_id, user.email, user.username)
                if not customer:
                    return {'error': 'Failed to create customer'}
            
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                customer=user.stripe_customer_id,
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': package['name'],
                            'description': f'Add {token_amount:,} tokens to your account'
                        },
                        'unit_amount': int(package['price'] * 100),
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=f"{os.environ.get('REPLIT_DOMAIN', 'http://localhost:5000')}/payment/tokens-success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{os.environ.get('REPLIT_DOMAIN', 'http://localhost:5000')}/payment/cancel",
                metadata={
                    'user_id': user_id,
                    'token_amount': token_amount,
                    'purchase_type': 'tokens'
                }
            )
            
            return {
                'session_id': session.id,
                'checkout_url': session.url
            }
            
        except stripe.error.StripeError as e:
            self.logger.error(f"Stripe error creating token purchase session: {e}")
            return {'error': f'Payment error: {str(e)}'}
        except Exception as e:
            self.logger.error(f"Error creating token purchase session: {e}")
            return {'error': 'Failed to create payment session'}
    
    def handle_token_purchase(self, session_id):
        """Handle successful token purchase"""
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            
            if session.payment_status == 'paid':
                user_id = int(session.metadata.get('user_id'))
                token_amount = int(session.metadata.get('token_amount'))
                
                # Add tokens to user's account (we'll implement this as extending their plan limits)
                user = User.query.get(user_id)
                if user:
                    # For token purchases, we'll extend the plan expiry or add bonus tokens
                    # This is a simplified implementation - you might want to track purchased tokens separately
                    if user.expires_at and user.expires_at > datetime.utcnow():
                        # Extend current plan by proportional time
                        days_to_add = max(7, token_amount // 10000)  # Minimum 7 days
                        user.expires_at += timedelta(days=days_to_add)
                    else:
                        # Grant Pro plan for token purchase
                        user.plan_status = 'pro'
                        user.expires_at = datetime.utcnow() + timedelta(days=30)
                    
                    db.session.commit()
                    
                    self.logger.info(f"Added {token_amount} tokens to user {user_id}")
                    
                    return {
                        'success': True,
                        'tokens_added': token_amount,
                        'new_expires_at': user.expires_at
                    }
            
            return {'error': 'Payment not completed'}
            
        except stripe.error.StripeError as e:
            self.logger.error(f"Stripe error handling token purchase: {e}")
            return {'error': f'Payment verification failed: {str(e)}'}
        except Exception as e:
            self.logger.error(f"Error handling token purchase: {e}")
            return {'error': 'Failed to process token purchase'}
    
    def get_plan_info(self, plan_type):
        """Get plan information"""
        return self.plans.get(plan_type, self.plans['free'])
    
    def get_all_plans(self):
        """Get all available plans"""
        return self.plans