import os

class Config:
    SECRET_KEY = 'your-secret-key-here'
    DEBUG = False
    
    # Mail Settings for Gmail
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = 'sky.remotes.co.uk@gmail.com'
    MAIL_PASSWORD = 'qpxl nkjq ffts wweh'  # Your App Password
    MAIL_DEFAULT_SENDER = ('Sky Remotes', 'info@skyremotes.co.uk')
    
    # IMAP settings
    IMAP_SERVER = 'imap.one.com'
    IMAP_PORT = 993
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = 'sqlite:///skyremotes.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False 