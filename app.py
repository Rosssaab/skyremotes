from flask import Flask, render_template, flash, redirect, url_for, jsonify, request, session, current_app
from flask_mail import Mail, Message
from forms import ContactForm
from config import Config
import smtplib
import jinja2
import logging
import os
import paypalrestsdk
from datetime import datetime, timedelta
import uuid
from flask_wtf.csrf import CSRFProtect
import traceback

# Set up logging with more detail
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

# Initialize CSRF protection
csrf = CSRFProtect(app)
mail = Mail(app)

# PayPal configuration
paypalrestsdk.configure({
    "mode": app.config['PAYPAL_MODE'],
    "client_id": app.config['PAYPAL_CLIENT_ID'],
    "client_secret": app.config['PAYPAL_CLIENT_SECRET']
})

# Add the nl2br filter
@app.template_filter('nl2br')
def nl2br(value):
    return jinja2.utils.markupsafe.Markup(value.replace('\n', '<br>'))

@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        try:
            # Send email to skyremotes
            admin_msg = Message(
                subject=f"Contact Form: {form.subject.data}",
                sender=app.config['MAIL_DEFAULT_SENDER'],
                recipients=['info@skyremotes.co.uk'],
                body=f"""
Name: {form.name.data}
Email: {form.email.data}
Subject: {form.subject.data}

Message:
{form.message.data}
                """
            )
            mail.send(admin_msg)
            
            # Send auto-reply to customer
            customer_msg = Message(
                subject="Thank you for contacting Sky Remotes",
                sender=app.config['MAIL_DEFAULT_SENDER'],
                recipients=[form.email.data],
                html=f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2>Thank you for contacting Sky Remotes</h2>
                    
                    <p>Dear {form.name.data},</p>
                    
                    <p>We have received your message and will get back to you as soon as possible. Our team typically responds within 24 hours during business days.</p>
                    
                    <p><strong>Your Message Details:</strong></p>
                    <ul>
                        <li>Subject: {form.subject.data}</li>
                        <li>Date: {datetime.now().strftime('%d-%m-%Y %H:%M')}</li>
                    </ul>
                    
                    <div style="background-color: #f8f9fa; padding: 15px; margin: 20px 0; border-radius: 5px;">
                        <h3>Quick Information:</h3>
                        <ul>
                            <li>Business Hours: Monday - Friday, 9:00 AM - 5:00 PM</li>
                            <li>Phone: +44 7737 463348</li>
                            <li>Email: info@skyremotes.co.uk</li>
                            <li>Same Day Dispatch for orders before 1PM</li>
                        </ul>
                    </div>
                    
                    <p>If you have an urgent inquiry, please don't hesitate to call us during business hours.</p>
                    
                    <p>Best regards,<br>
                    The Sky Remotes Team</p>
                </div>
                """
            )
            mail.send(customer_msg)
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': True})
            
            flash('Your message has been sent successfully!', 'success')
            return redirect(url_for('contact'))
            
        except Exception as e:
            logger.error(f'Error sending email: {str(e)}')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'error': str(e)})
            flash('Error sending message. Please try again.', 'error')
    
    return render_template('contact.html', form=form)

@app.route('/benefits')
def benefits():
    return render_template('benefits.html')

@app.route('/buy')
def buy():
    return render_template('buy.html')

@app.route('/cart')
def cart():
    return render_template('cart.html')

@app.route('/checkout')
def checkout():
    return render_template('checkout.html')

@app.route('/help')
def help():
    return render_template('help.html')

@app.route('/process-order', methods=['POST'])
def process_order():
    try:
        data = request.json
        
        # Generate order ID
        order_id = str(uuid.uuid4())[:8].upper()
        
        # Calculate estimated delivery
        now = datetime.now()
        if now.hour < 13:  # Before 1PM
            estimated_delivery = (now + timedelta(days=1)).strftime('%A, %B %d')
        else:
            estimated_delivery = (now + timedelta(days=2)).strftime('%A, %B %d')

        # Create order object
        order = {
            'id': order_id,
            'date': now.strftime('%Y-%m-%d %H:%M:%S'),
            'shipping': data['shippingDetails'],
            'paypal_order_id': data['orderID'],
            'quantity': data['quantity'],
            'total': data['total'],
            'estimated_delivery': estimated_delivery
        }

        # Send confirmation email
        try:
            msg = Message(
                subject=f'Order Confirmation - Sky Remotes #{order["id"]}',
                recipients=[order['shipping']['email']],
                sender=current_app.config['MAIL_DEFAULT_SENDER']
            )
            
            msg.html = render_template(
                'emails/order_confirmation.html',
                order=order
            )
            
            mail.send(msg)
            print(f"Email sent successfully to {order['shipping']['email']}")  # Debug log
            
        except Exception as e:
            print(f"Failed to send email: {str(e)}")  # Debug log
            # Continue processing even if email fails
            
        # Store order in session for success page
        session['last_order'] = order

        return jsonify({
            "status": "success",
            "message": "Order processed successfully",
            "order_id": order_id
        })
        
    except Exception as e:
        print(f"Order processing error: {str(e)}")  # Debug log
        return jsonify({
            "status": "error",
            "message": "There was a problem processing your order"
        }), 500

@app.route('/order-success')
def order_success():
    order = session.get('last_order')
    if not order:
        return redirect(url_for('home'))
    
    # Clear the order from session after displaying
    session.pop('last_order', None)
    
    return render_template('order-success.html', order=order)

# Add a test route
@app.route('/test-mail-config')
def test_mail_config():
    config_info = {
        'MAIL_SERVER': app.config['MAIL_SERVER'],
        'MAIL_PORT': app.config['MAIL_PORT'],
        'MAIL_USE_TLS': app.config['MAIL_USE_TLS'],
        'MAIL_USERNAME': app.config['MAIL_USERNAME'],
        'MAIL_DEFAULT_SENDER': app.config['MAIL_DEFAULT_SENDER']
    }
    logger.debug(f'Mail configuration: {config_info}')
    return jsonify(config_info)

@app.route('/test-email')
def test_email():
    try:
        logger.debug('Testing email configuration...')
        msg = Message(
            subject='Test Email',
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=['info@skyremotes.co.uk'],
            body='This is a test email'
        )
        
        logger.debug('Attempting to send test email...')
        mail.send(msg)
        logger.debug('Test email sent successfully')
        return 'Test email sent successfully! Check logs for details.'
    except Exception as e:
        error_details = f'Error: {str(e)}\n\nTraceback:\n{traceback.format_exc()}'
        logger.error(error_details)
        return f'Error sending test email: {error_details}'

if __name__ == '__main__':
    # Log the configuration at startup
    logger.debug('Starting application with configuration:')
    logger.debug(f'MAIL_SERVER: {app.config["MAIL_SERVER"]}')
    logger.debug(f'MAIL_PORT: {app.config["MAIL_PORT"]}')
    logger.debug(f'MAIL_USE_TLS: {app.config["MAIL_USE_TLS"]}')
    logger.debug(f'MAIL_USERNAME: {app.config["MAIL_USERNAME"]}')
    
    app.run(host='127.0.0.1', port=8091, debug=True) 