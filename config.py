import os

class Config:
    SECRET_KEY = 'your-secret-key-here'
    DEBUG = False
    
    # Mail Settings for one.com
    MAIL_SERVER = 'send.one.com'  # Changed from imap to send
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = 'info@skyremotes.co.uk'
    MAIL_PASSWORD = 'Oracle69#'  # Your one.com email password
    MAIL_DEFAULT_SENDER = 'Sky Remotes <info@skyremotes.co.uk>'
    
    # IMAP settings
    IMAP_SERVER = 'imap.one.com'
    IMAP_PORT = 993
    
    # Database settings for SQL Server
    DB_SERVER = 'MICROWEBSERVER\\SQLEXPRESS'
    DB_NAME = 'SkyRemotes'
    DB_USER = 'SkyAdm'
    DB_PASSWORD = 'Oracle69#'
    
    # SQL Server connection string
    SQLALCHEMY_DATABASE_URI = f'mssql+pyodbc://{DB_USER}:{DB_PASSWORD}@{DB_SERVER}/{DB_NAME}?driver=SQL+Server'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # PayPal settings
    PAYPAL_MODE = 'live'  # Change to 'live' for production
    PAYPAL_CLIENT_ID = 'AV8K6W4_wFN8K2yovwbnJGUA9kCpe-kQ7gb2NBqvjQVzoe8tVlp8V0ZX9x9D4AojNsb3u3NYrQCCml3A'
    PAYPAL_CLIENT_SECRET = 'ELnwyrcbs7t0C2PFZsEetrcNR9XeooiOdy-SxCbmWB0pGK8u8HTwM_SqW2FGoa-cNJ3WxjU4R6tl6HVp'

    # Admin credentials
    ADMIN_USERNAME = 'TedAdmin'
    ADMIN_PASSWORD = '1loveR055'  # You should change this to a strong password
    ADMIN_EMAIL = 'info@skyremotes.co.uk'