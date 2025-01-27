from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, Length

class ContactForm(FlaskForm):
    name = StringField('Name', validators=[
        DataRequired(),
        Length(min=2, max=50, message="Name must be between 2 and 50 characters")
    ])
    
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message="Please enter a valid email address")
    ])
    
    subject = SelectField('Subject', choices=[
        ('Request Free eBook', 'Request Free eBook'),
        ('Water Sample Request', 'Request Water Sample'),
        ('Machine Demo Request', 'Book a Machine Demo'),
        ('Price Enquiry', 'Get Pricing Information'),
        ('Product Information', 'General Product Information'),
        ('Business Opportunity', 'Business Opportunity'),
    ], validators=[DataRequired()])
    
    message = TextAreaField('Message', validators=[
        DataRequired(),
        Length(min=10, max=2000, message="Message must be between 10 and 2000 characters")
    ])
    
    submit = SubmitField('Send Message') 