from flask import Flask, render_template, flash, redirect, url_for
from flask_mail import Mail, Message
from forms import ContactForm
from config import Config
import smtplib
import jinja2

app = Flask(__name__)
app.config.from_object(Config)
mail = Mail(app)

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
            # Send the form data to site owner
            msg = Message(
                subject=f"Contact Form: {form.subject.data}",
                recipients=['info@skyremotes.uk'],
                body=f"Name: {form.name.data}\nEmail: {form.email.data}\nSubject: {form.subject.data}\n\nMessage:\n{form.message.data}"
            )
            # Add headers to prevent spam classification
            msg.extra_headers = {
                "List-Unsubscribe": "<mailto:info@skyremotes.uk>",
                "Precedence": "bulk",
                "X-Auto-Response-Suppress": "OOF",
                "Auto-Submitted": "auto-generated"
            }
            
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
                    <p><small>This email was sent from the skyremotes UK contact form.</small></p>
                </body>
            </html>
            """
            
            mail.send(msg)
            
            # Auto-reply with similar headers
            auto_reply = Message(
                subject="Thank you for contacting skyremotes UK",
                recipients=[form.email.data],
                sender=("skyremotes UK", "info@skyremotes.uk")
            )
            auto_reply.extra_headers = {
                "List-Unsubscribe": "<mailto:info@skyremotes.uk>",
                "Precedence": "bulk",
                "X-Auto-Response-Suppress": "OOF",
                "Auto-Submitted": "auto-generated"
            }
            auto_reply.html = f"""
            <html>
                <body>
                    <h2>Thank you for contacting skyremotes UK</h2>
                    <p>Dear {form.name.data},</p>
                    <p>We have received your message and will get back to you shortly.</p>
                    <h3>Your message details:</h3>
                    <p><strong>Subject:</strong> {form.subject.data}</p>
                    <p><strong>Message:</strong><br>{form.message.data}</p>
                    <hr>
                    <p>Best regards,<br>
                    skyremotes UK Team<br>
                    <a href="mailto:info@skyremotes.uk">info@skyremotes.uk</a></p>
                </body>
            </html>
            """
            
            mail.send(auto_reply)
            
            flash('Your message has been sent successfully!\nWe will get back to you soon.\nCheck your spam folder', 'success')
            return redirect(url_for('contact'))
        except Exception as e:
            flash(f'Error: Could not authenticate with email server. Please try again later or email us directly.', 'error')
            if app.debug:
                print(f"Mail error: {str(e)}")
    return render_template('contact.html', form=form)

@app.route('/benefits')
def benefits():
    return render_template('benefits.html')

if __name__ == '__main__':
    app.run(debug=True, port=8091) 