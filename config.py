import os

class Config:
    SECRET_KEY = 'your-secret-key-here'
    DEBUG = False
    
    # Mail Settings for one.com
    MAIL_SERVER = 'send.one.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = 'info@skyremotes.co.uk'
    MAIL_PASSWORD = 'Oracle69#'
    MAIL_DEFAULT_SENDER = 'Sky Remotes <info@skyremotes.co.uk>'
    
    # Add debug settings
    MAIL_DEBUG = True  # Enable mail debug
    MAIL_SUPPRESS_SEND = False  # Make sure emails are actually sent
    
    # IMAP settings
    IMAP_SERVER = 'imap.one.com'
    IMAP_PORT = 993
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = 'sqlite:///skyremotes.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # PayPal settings
    PAYPAL_MODE = 'live'  # Change to 'live' for production
    PAYPAL_CLIENT_ID = 'AcHQ2A2MZh1YEQzDVnULfe7L6FkKE793ZiIQ-pT35daEQwid5_6l2ZX4_jUR_8JqEx-J1umiFJ8iF6Y1'
    PAYPAL_CLIENT_SECRET = 'EIpxrhYmzqq__8n8xwiacv8HVuhCBH9hCaXK0C_9W4L_aAwCXl2azD7TfDUJZ2nEu1Ntg8hnB9I6gr74' 