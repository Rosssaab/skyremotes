from flask import Flask, render_template, flash, redirect, url_for, jsonify, request, session
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

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)
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
            logger.debug('Attempting to send email...')
            logger.debug(f'Mail settings: SERVER={app.config["MAIL_SERVER"]}, PORT={app.config["MAIL_PORT"]}')
            logger.debug(f'From: {app.config["MAIL_USERNAME"]}')
            
            # Send the form data to site owner
            msg = Message(
                subject=f"Contact Form: {form.subject.data}",
                recipients=['sky.remotes.co.uk@gmail.com'],
                body=f"Name: {form.name.data}\nEmail: {form.email.data}\nSubject: {form.subject.data}\n\nMessage:\n{form.message.data}"
            )
            logger.debug('Message object created')
            
            # Add headers to prevent spam classification
            msg.extra_headers = {
                "List-Unsubscribe": "<mailto:sky.remotes.co.uk@gmail.com>",
                "Precedence": "bulk",
                "X-Auto-Response-Suppress": "OOF",
                "Auto-Submitted": "auto-generated"
            }
            logger.debug('Headers added')
            
            # Add a more professional format
            msg.html = f"""
            <html>
                <body>
                    <h2>New Contact Form Submission</h2>
                    <p><strong>Name:</strong> {form.name.data}</p>
                    <p><strong>Email:</strong> {form.email.data}</p>
                    <p><strong>Subject:</strong> {form.subject.data}</p>
                    <h3>Message:</h3>
                    <p>{form.message.data}</p>
                    <hr>
                    <p><small>This email was sent from the skyremotes contact form.</small></p>
                </body>
            </html>
            """
            logger.debug('HTML content added')
            
            try:
                mail.send(msg)
                logger.debug('Main email sent successfully')
            except Exception as e:
                logger.error(f'Error sending main email: {str(e)}')
                raise
            
            # Auto-reply with similar headers
            try:
                auto_reply = Message(
                    subject="Thank you for contacting Sky Remotes",
                    recipients=[form.email.data],
                    sender=("Sky Remotes", "sky.remotes.co.uk@gmail.com")
                )
                auto_reply.extra_headers = {
                    "List-Unsubscribe": "<mailto:sky.remotes.co.uk@gmail.com>",
                    "Precedence": "bulk",
                    "X-Auto-Response-Suppress": "OOF",
                    "Auto-Submitted": "auto-generated"
                }
                auto_reply.html = f"""
                <html>
                    <body>
                        <h2>Thank you for contacting Sky Remotes</h2>
                        <p>Dear {form.name.data},</p>
                        <p>We have received your message and will get back to you shortly.</p>
                        <h3>Your message details:</h3>
                        <p><strong>Subject:</strong> {form.subject.data}</p>
                        <p><strong>Message:</strong><br>{form.message.data}</p>
                        <hr>
                        <p>Best regards,<br>
                        Sky Remotes Team<br>
                        <a href="mailto:sky.remotes.co.uk@gmail.com">sky.remotes.co.uk@gmail.com</a></p>
                    </body>
                </html>
                """
                
                mail.send(auto_reply)
                logger.debug('Auto-reply sent successfully')
            except Exception as e:
                logger.error(f'Error sending auto-reply: {str(e)}')
                # Continue even if auto-reply fails
            
            flash('Your message has been sent successfully!\nWe will get back to you soon.\nCheck your spam folder', 'success')
            return redirect(url_for('contact'))
        except Exception as e:
            logger.error(f'Mail error: {str(e)}')
            flash(f'Error: Could not authenticate with email server. Please try again later or email us directly. Error: {str(e)}', 'error')
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
    data = request.json
    
    # Generate order ID
    order_id = str(uuid.uuid4())[:8].upper()
    
    # Calculate estimated delivery (next business day if ordered before 1PM)
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
        send_order_confirmation(order)
    except Exception as e:
        app.logger.error(f"Failed to send confirmation email: {str(e)}")

    # Store order in session for success page
    session['last_order'] = order

    return jsonify({
        "status": "success",
        "message": "Order processed successfully",
        "order_id": order_id
    })

@app.route('/order-success')
def order_success():
    order = session.get('last_order')
    if not order:
        return redirect(url_for('home'))
    
    # Clear the order from session after displaying
    session.pop('last_order', None)
    
    return render_template('order-success.html', order=order)

def send_order_confirmation(order):
    try:
        msg = Message(
            subject=f"Order Confirmation - Sky Remotes #{order['id']}",
            recipients=[order['shipping']['email']]
        )
        
        msg.html = render_template(
            'emails/order_confirmation.html',
            order=order
        )
        
        print(f"Attempting to send email to {order['shipping']['email']}")  # Debug log
        mail.send(msg)
        print("Email sent successfully")  # Debug log
        
    except Exception as e:
        print(f"Email error: {str(e)}")  # Debug log
        # Log the full error details
        import traceback
        print(traceback.format_exc())
        raise  # Re-raise the exception to see it in the Flask logs

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8091, debug=True) 