import logging
import ssl
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from app.config import settings

# Bypass macOS Python SSL Certificate verification for outbound requests
ssl._create_default_https_context = ssl._create_unverified_context

logger = logging.getLogger(__name__)

def send_reset_email(to_email: str, reset_link: str) -> bool:
    """
    Send an automated password reset email via SendGrid.
    """
    if not settings.SENDGRID_API_KEY:
        logger.warning(f"No SENDGRID_API_KEY configured. Mocking email to: {to_email}")
        print("\n" + "="*50)
        print(f"📧 Fallback Mock Email Sent to: {to_email}")
        print(f"\n👉 {reset_link}")
        print("="*50 + "\n")
        return False
        
    message = Mail(
        from_email='hardiksingh2775@gmail.com',  # SendGrid Verified Sender
        to_emails=to_email,
        subject='Reset your WANDR Password',
        html_content=f'''
        <div style="font-family: sans-serif; max-width: 600px; margin: auto; padding: 20px; text-align: center;">
            <h2 style="color: #2563eb; letter-spacing: 2px;">WANDR</h2>
            <h3 style="color: #374151;">Password Reset Request</h3>
            <p style="color: #4b5563; font-size: 16px; margin-bottom: 30px;">
                We received a request to reset your password. Click the button below to choose a new one:
            </p>
            <p>
                <a href="{reset_link}" style="background-color: #2563eb; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px;">Change Password</a>
            </p>
            <p style="color: #9ca3af; font-size: 12px; margin-top: 40px;">
                If you didn't request a password reset, you can safely ignore this email. This link will expire in 1 hour.
            </p>
        </div>
        '''
    )
    
    try:
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        logger.info(f"SendGrid response: {response.status_code}")
        return response.status_code in [200, 201, 202]
    except Exception as e:
        logger.error(f"Failed to send email via SendGrid: {str(e)}")
        # Print fallback to console so developer can still access link
        print("\n" + "="*50)
        print(f"📧 Fallback Mock Email Sent to: {to_email}")
        print(f"\n👉 {reset_link}")
        print("="*50 + "\n")
        return False


def send_verification_email(to_email: str, code: str) -> bool:
    """
    Send a 6-digit verification code for email verification on signup.
    """
    if not settings.SENDGRID_API_KEY:
        logger.warning(f"No SENDGRID_API_KEY configured. Mocking verification email to: {to_email}")
        print("\n" + "="*50)
        print(f"📧 Verification Code for {to_email}: {code}")
        print("="*50 + "\n")
        return False

    message = Mail(
        from_email='hardiksingh2775@gmail.com',
        to_emails=to_email,
        subject='Verify your WANDR Account',
        html_content=f'''
        <div style="font-family: sans-serif; max-width: 600px; margin: auto; padding: 20px; text-align: center;">
            <h2 style="color: #2563eb; letter-spacing: 2px;">WANDR</h2>
            <h3 style="color: #374151;">Email Verification</h3>
            <p style="color: #4b5563; font-size: 16px;">Your verification code is:</p>
            <p style="font-size: 36px; font-weight: bold; letter-spacing: 8px; color: #2563eb; margin: 20px 0;">{code}</p>
            <p style="color: #9ca3af; font-size: 12px; margin-top: 40px;">This code expires in 15 minutes.</p>
        </div>
        '''
    )
    try:
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        return response.status_code in [200, 201, 202]
    except Exception as e:
        logger.error(f"Failed to send verification email: {str(e)}")
        print("\n" + "="*50)
        print(f"📧 Verification Code for {to_email}: {code}")
        print("="*50 + "\n")
        return False


def send_otp_email(to_email: str, code: str, purpose: str = "password change") -> bool:
    """
    Send a 6-digit OTP code for password change.
    """
    if not settings.SENDGRID_API_KEY:
        logger.warning(f"No SENDGRID_API_KEY. Mocking OTP email to: {to_email}")
        print("\n" + "="*50)
        print(f"📧 OTP Code ({purpose}) for {to_email}: {code}")
        print("="*50 + "\n")
        return False

    message = Mail(
        from_email='hardiksingh2775@gmail.com',
        to_emails=to_email,
        subject=f'WANDR — Your {purpose.title()} Code',
        html_content=f'''
        <div style="font-family: sans-serif; max-width: 600px; margin: auto; padding: 20px; text-align: center;">
            <h2 style="color: #2563eb; letter-spacing: 2px;">WANDR</h2>
            <h3 style="color: #374151;">{purpose.title()} Request</h3>
            <p style="color: #4b5563; font-size: 16px;">Your security code is:</p>
            <p style="font-size: 36px; font-weight: bold; letter-spacing: 8px; color: #2563eb; margin: 20px 0;">{code}</p>
            <p style="color: #9ca3af; font-size: 12px; margin-top: 40px;">This code expires in 15 minutes. Do not share it with anyone.</p>
        </div>
        '''
    )
    try:
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        return response.status_code in [200, 201, 202]
    except Exception as e:
        logger.error(f"Failed to send OTP email: {str(e)}")
        print("\n" + "="*50)
        print(f"📧 OTP Code ({purpose}) for {to_email}: {code}")
        print("="*50 + "\n")
        return False
