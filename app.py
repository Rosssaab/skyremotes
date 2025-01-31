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
from flask_wtf.csrf import CSRFProtect, generate_csrf
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

@csrf.exempt
@app.route('/process-order', methods=['POST'])
def process_order():
    try:
        data = request.get_json()
        app.logger.info('Processing order...')
        app.logger.info(f'PayPal Transaction ID: {data.get("transactionID")}')
        app.logger.info(f'PayPal Payment Status: {data.get("paymentStatus")}')

        # Verify payment status
        if data.get('paymentStatus') != 'COMPLETED':
            raise Exception('Payment not completed')

        try:
            # Create customer confirmation email
            customer_msg = Message(
                'Your Sky Remote Order Confirmation',
                sender='Sky Remotes <info@skyremotes.co.uk>',
                recipients=[data['shippingDetails']['email']]
            )
            
            # Prepare order data with transaction details
            order_data = {
                'id': data['orderID'],
                'transaction_id': data.get('transactionID'),
                'shipping': data['shippingDetails'],
                'quantity': data['quantity'],
                'total': float(data['total']),
                'date': datetime.now().strftime('%d-%m-%Y %H:%M'),
                'estimated_delivery': '2-3 working days',
                'payment_method': 'PayPal' if data.get('transactionID') else 'Card'
            }

            app.logger.info(f'Order data prepared: {order_data}')

            # Send customer confirmation
            customer_msg.html = render_template(
                'emails/order_confirmation.html',
                order=order_data
            )
            mail.send(customer_msg)
            app.logger.info(f'Customer confirmation sent to {data["shippingDetails"]["email"]}')

            # Send admin notification
            admin_msg = Message(
                f'New Order: {data["orderID"]}',
                sender='Sky Remotes <info@skyremotes.co.uk>',
                recipients=['info@skyremotes.co.uk']
            )
            
            admin_msg.html = render_template(
                'emails/admin_order_notification.html',
                order=order_data
            )
            mail.send(admin_msg)
            app.logger.info('Admin notification sent')

        except Exception as e:
            app.logger.error(f'Email error: {str(e)}')
            app.logger.error(traceback.format_exc())
            
        return jsonify({
            'status': 'success',
            'message': 'Order processed successfully',
            'transaction_id': data.get('transactionID')
        })

    except Exception as e:
        app.logger.error(f'Order processing error: {str(e)}')
        app.logger.error(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': str(e)
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
        msg = Message(
            'Test Email from Sky Remotes',
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=['info@skyremotes.co.uk']
        )
        msg.body = 'This is a test email from Sky Remotes website'
        mail.send(msg)
        return 'Test email sent successfully!'
    except Exception as e:
        app.logger.error(f'Test email error: {str(e)}')
        return f'Error sending test email: {str(e)}'

@app.route('/test-connection')
def test_connection():
    try:
        # Test database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT @@version;")
        version = cursor.fetchone()
        cursor.close()
        conn.close()

        # Test email
        try:
            msg = Message(
                'Test Email',
                sender='info@skyremotes.co.uk',
                recipients=['info@skyremotes.co.uk']
            )
            msg.body = "This is a test email from Sky Remotes"
            mail.send(msg)
            email_status = "Email test successful"
        except Exception as e:
            email_status = f"Email test failed: {str(e)}"

        return jsonify({
            'status': 'success',
            'message': 'Connection test completed',
            'details': {
                'database': f"Connected (Version: {version[0] if version else 'Unknown'})",
                'email': email_status
            }
        })
    except Exception as e:
        app.logger.error(f'Test connection error: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/remove-from-cart', methods=['POST'])
def remove_from_cart():
    try:
        return jsonify({
            'status': 'success',
            'message': 'Item removed from cart'
        })
    except Exception as e:
        app.logger.error(f'Error removing item from cart: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    # Log the configuration at startup
    logger.debug('Starting application with configuration:')
    logger.debug(f'MAIL_SERVER: {app.config["MAIL_SERVER"]}')
    logger.debug(f'MAIL_PORT: {app.config["MAIL_PORT"]}')
    logger.debug(f'MAIL_USE_TLS: {app.config["MAIL_USE_TLS"]}')
    logger.debug(f'MAIL_USERNAME: {app.config["MAIL_USERNAME"]}')
    
    app.run(host='127.0.0.1', port=8091, debug=True) 