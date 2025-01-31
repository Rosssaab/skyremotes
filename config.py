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
    PAYPAL_CLIENT_ID = 'AV8K6W4_wFN8K2yovwbnJGUA9kCpe-kQ7gb2NBqvjQVzoe8tVlp8V0ZX9x9D4AojNsb3u3NYrQCCml3A'
    PAYPAL_CLIENT_SECRET = 'ELnwyrcbs7t0C2PFZsEetrcNR9XeooiOdy-SxCbmWB0pGK8u8HTwM_SqW2FGoa-cNJ3WxjU4R6tl6HVp' 