from flask import Flask, render_template, flash, redirect, url_for, jsonify, request, session, current_app, send_from_directory
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
import pyodbc
from utils.order_processor import process_new_order
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash
import requests

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

# Exempt the process-order route from CSRF
@csrf.exempt
@app.route('/process_order', methods=['POST'])
def process_order():
    try:
        data = request.json
        result = process_new_order(
            shipping_details=data['shippingDetails'],
            payment_details=data['paypalDetails'],
            total_amount=data['total']
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'order_id': result['order_id'],
                'redirect': url_for('order_success')
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500

    except Exception as e:
        logger.error(f'Order processing error: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/test_payment', methods=['POST'])
@csrf.exempt
def test_payment():
    try:
        logger.debug('Received test payment request')
        data = request.json
        logger.debug(f'Payment data received: {data}')
        
        result = process_new_order(
            shipping_details=data['shippingDetails'],
            payment_details={'id': 'TEST-PAYMENT', 'status': 'COMPLETED'},
            total_amount=data['total']
        )
        
        logger.debug(f'Order processing result: {result}')
        
        if result['success']:
            return jsonify({
                'success': True,
                'order_id': result['order_id'],
                'redirect': url_for('order_success')
            })
        else:
            logger.error(f'Order processing failed: {result["error"]}')
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500

    except Exception as e:
        logger.error(f'Test payment error: {str(e)}')
        logger.error(f'Full traceback: {traceback.format_exc()}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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

def update_order_status(order_id, new_status_id, notes=None, updated_by="System"):
    try:
        conn = pyodbc.connect('DRIVER={SQL Server};SERVER=MICROWEBSERVER\\SQLEXPRESS;DATABASE=SkyRemotes;UID=SkyAdm;PWD=Oracle69#')
        cursor = conn.cursor()

        # Update Orders table
        cursor.execute("""
            UPDATE Orders 
            SET CurrentStatusID = ? 
            WHERE OrderID = ?
        """, new_status_id, order_id)

        # Add status history record
        cursor.execute("""
            INSERT INTO OrderStatusHistory (OrderID, StatusID, StatusDate, UpdatedBy, Notes)
            VALUES (?, ?, GETDATE(), ?, ?)
        """, order_id, new_status_id, updated_by, notes)

        conn.commit()
        return True

    except Exception as e:
        logger.error(f'Status update error: {str(e)}')
        return False

    finally:
        if 'conn' in locals():
            conn.close()

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin', methods=['GET', 'POST'])
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username', '').lower()
        password = request.form.get('password')
        
        if username == app.config['ADMIN_USERNAME'].lower() and password == app.config['ADMIN_PASSWORD']:
            session['admin_logged_in'] = True
            return redirect(url_for('orders'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('admin_login.html')

@app.route('/orders')
@login_required
def orders():
    try:
        conn = pyodbc.connect(f'DRIVER={{SQL Server}};SERVER={app.config["DB_SERVER"]};DATABASE={app.config["DB_NAME"]};UID={app.config["DB_USER"]};PWD={app.config["DB_PASSWORD"]}')
        cursor = conn.cursor()
        
        # Get filters from query parameters
        status_filter = request.args.get('status', '')
        date_filter = request.args.get('date', '')
        logger.debug(f'Status filter: {status_filter}, Date filter: {date_filter}')
        
        # Base query
        base_query = """
            SELECT 
                o.OrderID as id,
                o.OrderDate as date,
                c.FirstName + ' ' + c.LastName as customer_name,
                o.TotalAmount as total,
                s.StatusName as status,
                o.Notes as notes
            FROM Orders o
            JOIN Customers c ON o.CustomerID = c.CustomerID
            JOIN OrderStatus s ON o.CurrentStatusID = s.StatusID
            WHERE 1=1
        """
        
        params = []
        
        # Add status filter if provided
        if status_filter:
            base_query += " AND o.CurrentStatusID = ?"
            params.append(int(status_filter))
            
        # Add date filter if provided
        if date_filter:
            base_query += " AND CONVERT(date, o.OrderDate) = ?"
            params.append(date_filter)
            
        # Add order by
        base_query += " ORDER BY o.OrderDate DESC"
        
        logger.debug(f'Executing query with params: {params}')
        cursor.execute(base_query, params)
        
        orders = []
        for row in cursor.fetchall():
            orders.append({
                'id': row.id,
                'date': row.date,
                'customer_name': row.customer_name,
                'total': float(row.total) if row.total else 0.0,
                'status': row.status,
                'notes': row.notes
            })
        
        # Get statuses for dropdown
        cursor.execute("SELECT StatusID, StatusName FROM OrderStatus ORDER BY StatusID")
        statuses = []
        for row in cursor.fetchall():
            statuses.append({
                'id': row.StatusID,
                'name': row.StatusName
            })
        
        return render_template('orders.html', 
                             orders=orders, 
                             statuses=statuses, 
                             selected_status=status_filter,
                             selected_date=date_filter)
        
    except Exception as e:
        logger.error(f'Error fetching orders: {str(e)}')
        logger.error(f'Full traceback: {traceback.format_exc()}')
        flash('Error loading orders', 'error')
        return redirect(url_for('home'))
        
    finally:
        if 'conn' in locals():
            conn.close()

# Update status route
@app.route('/update_order_status', methods=['POST'])
@login_required
def update_order_status():
    try:
        data = request.get_json()
        order_id = data.get('order_id')
        status_id = data.get('status_id')
        notes = data.get('notes')

        conn = pyodbc.connect(f'DRIVER={{SQL Server}};SERVER={app.config["DB_SERVER"]};DATABASE={app.config["DB_NAME"]};UID={app.config["DB_USER"]};PWD={app.config["DB_PASSWORD"]}')
        cursor = conn.cursor()

        # Update the order status
        cursor.execute("""
            UPDATE dbo.Orders 
            SET CurrentStatusID = ? 
            WHERE OrderID = ?
        """, status_id, order_id)

        # Add entry to status history
        cursor.execute("""
            INSERT INTO dbo.OrderStatusHistory 
            (OrderID, StatusID, StatusDate, UpdatedBy, Notes)
            VALUES (?, ?, GETDATE(), ?, ?)
        """, order_id, status_id, session.get('admin_username', 'admin'), notes)

        conn.commit()
        
        return jsonify({'success': True})

    except Exception as e:
        logger.error(f'Error updating order status: {str(e)}')
        return jsonify({'success': False, 'error': str(e)})

    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('home'))

@app.route('/order_details/<int:order_id>')
@login_required
def order_details(order_id):
    try:
        logger.debug(f'Fetching order details for order_id: {order_id}')
        conn = pyodbc.connect(f'DRIVER={{SQL Server}};SERVER={app.config["DB_SERVER"]};DATABASE={app.config["DB_NAME"]};UID={app.config["DB_USER"]};PWD={app.config["DB_PASSWORD"]}')
        cursor = conn.cursor()
        
        # Get order and customer details
        query = """
            SELECT 
                o.OrderID,
                o.OrderDate,
                o.TotalAmount,
                o.PayPalTransactionID,
                o.PayPalStatus,
                o.Notes,
                o.CurrentStatusID,
                s.StatusName as Status,
                c.FirstName + ' ' + c.LastName as CustomerName,
                c.Email as CustomerEmail,
                c.Address1 as CustomerAddress,
                CASE 
                    WHEN c.Address2 IS NOT NULL AND c.Address2 <> '' 
                    THEN CHAR(13) + CHAR(10) + c.Address2 
                    ELSE '' 
                END as CustomerAddress2,
                c.City as CustomerCity,
                c.PostCode as CustomerPostcode
            FROM Orders o
            JOIN Customers c ON o.CustomerID = c.CustomerID
            JOIN OrderStatus s ON o.CurrentStatusID = s.StatusID
            WHERE o.OrderID = ?
        """
        logger.debug(f'Executing query: {query}')
        cursor.execute(query, order_id)
        
        order_data = cursor.fetchone()
        if not order_data:
            logger.error(f'No order found for order_id: {order_id}')
            flash('Order not found', 'error')
            return redirect(url_for('orders'))
            
        logger.debug(f'Order data fetched: {order_data}')
            
        # Get order items
        items_query = """
            SELECT 
                ProductName,
                Quantity,
                UnitPrice,
                TotalPrice
            FROM OrderItems
            WHERE OrderID = ?
        """
        logger.debug(f'Executing items query: {items_query}')
        cursor.execute(items_query, order_id)
        
        items = []
        for item in cursor.fetchall():
            items.append({
                'product_name': item.ProductName,
                'quantity': item.Quantity,
                'unit_price': float(item.UnitPrice),
                'total_price': float(item.TotalPrice)
            })
        logger.debug(f'Items fetched: {items}')
            
        # Get all possible statuses
        cursor.execute("SELECT StatusID, StatusName FROM OrderStatus ORDER BY StatusID")
        statuses = [{'id': row.StatusID, 'name': row.StatusName} for row in cursor.fetchall()]
        logger.debug(f'Statuses fetched: {statuses}')
        
        order = {
            'id': order_data.OrderID,
            'date': order_data.OrderDate,
            'total': float(order_data.TotalAmount),
            'paypal_id': order_data.PayPalTransactionID,
            'paypal_status': order_data.PayPalStatus,
            'notes': order_data.Notes,
            'status': order_data.Status,
            'status_id': order_data.CurrentStatusID,
            'customer_name': order_data.CustomerName,
            'customer_email': order_data.CustomerEmail,
            'customer_address': order_data.CustomerAddress + order_data.CustomerAddress2,
            'customer_city': order_data.CustomerCity,
            'customer_postcode': order_data.CustomerPostcode
        }
        logger.debug(f'Final order object: {order}')
        
        return render_template('order_details.html', order=order, items=items, statuses=statuses)
        
    except Exception as e:
        logger.error(f'Error fetching order details: {str(e)}')
        logger.error(f'Full traceback: {traceback.format_exc()}')
        flash('Error loading order details', 'error')
        return redirect(url_for('orders'))
        
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/status_colors_test')
@login_required
def status_colors_test():
    return render_template('status_colors_test.html')

# Add this route to handle notes updates
@app.route('/update_order_notes', methods=['POST'])
@login_required
def update_order_notes():
    try:
        data = request.get_json()
        order_id = data.get('order_id')
        notes = data.get('notes')

        if not order_id:
            return jsonify({'success': False, 'error': 'Order ID is required'})

        conn = pyodbc.connect(f'DRIVER={{SQL Server}};SERVER={app.config["DB_SERVER"]};DATABASE={app.config["DB_NAME"]};UID={app.config["DB_USER"]};PWD={app.config["DB_PASSWORD"]}')
        cursor = conn.cursor()
        
        # Update the Notes field in the Orders table
        cursor.execute("""
            UPDATE dbo.Orders 
            SET Notes = ? 
            WHERE OrderID = ?
        """, (notes, order_id))
        
        conn.commit()
        return jsonify({'success': True})

    except Exception as e:
        logger.error(f'Error updating notes: {str(e)}')
        return jsonify({'success': False, 'error': str(e)})

    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/invoice_print/<int:order_id>')
@login_required
def invoice_print(order_id):
    try:
        conn = pyodbc.connect(f'DRIVER={{SQL Server}};SERVER={app.config["DB_SERVER"]};DATABASE={app.config["DB_NAME"]};UID={app.config["DB_USER"]};PWD={app.config["DB_PASSWORD"]}')
        cursor = conn.cursor()
        
        # Get order and customer details
        query = """
            SELECT 
                o.OrderID,
                o.OrderDate,
                o.TotalAmount,
                o.PayPalTransactionID,
                o.PayPalStatus,
                o.Notes,
                o.CurrentStatusID,
                s.StatusName as Status,
                c.FirstName + ' ' + c.LastName as CustomerName,
                c.Email as CustomerEmail,
                c.Address1 as CustomerAddress,
                CASE 
                    WHEN c.Address2 IS NOT NULL AND c.Address2 <> '' 
                    THEN CHAR(13) + CHAR(10) + c.Address2 
                    ELSE '' 
                END as CustomerAddress2,
                c.City as CustomerCity,
                c.PostCode as CustomerPostcode
            FROM Orders o
            JOIN Customers c ON o.CustomerID = c.CustomerID
            JOIN OrderStatus s ON o.CurrentStatusID = s.StatusID
            WHERE o.OrderID = ?
        """
        cursor.execute(query, order_id)
        
        order_data = cursor.fetchone()
        if not order_data:
            flash('Order not found', 'error')
            return redirect(url_for('orders'))
            
        # Get order items
        cursor.execute("""
            SELECT 
                ProductName,
                Quantity,
                UnitPrice,
                TotalPrice
            FROM OrderItems
            WHERE OrderID = ?
        """, order_id)
        
        items = []
        for item in cursor.fetchall():
            items.append({
                'product_name': item.ProductName,
                'quantity': item.Quantity,
                'unit_price': float(item.UnitPrice),
                'total_price': float(item.TotalPrice)
            })
            
        order = {
            'id': order_data.OrderID,
            'date': order_data.OrderDate,
            'total': float(order_data.TotalAmount),
            'paypal_id': order_data.PayPalTransactionID,
            'paypal_status': order_data.PayPalStatus,
            'notes': order_data.Notes,
            'status': order_data.Status,
            'status_id': order_data.CurrentStatusID,
            'customer_name': order_data.CustomerName,
            'customer_email': order_data.CustomerEmail,
            'customer_address': order_data.CustomerAddress + order_data.CustomerAddress2,
            'customer_city': order_data.CustomerCity,
            'customer_postcode': order_data.CustomerPostcode
        }
        
        return render_template('invoice_print.html', order=order, items=items)
        
    except Exception as e:
        logger.error(f'Error fetching invoice details: {str(e)}')
        return 'Error loading invoice', 500
        
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory('static', 'sitemap.xml', mimetype='application/xml')

@app.route('/robots.txt')
def robots():
    return send_from_directory('static', 'robots.txt', mimetype='text/plain')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/visitors')
@login_required
def visitors():
    try:
        conn = pyodbc.connect(f'DRIVER={{SQL Server}};SERVER={app.config["DB_SERVER"]};DATABASE={app.config["DB_NAME"]};UID={app.config["DB_USER"]};PWD={app.config["DB_PASSWORD"]}')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                v.VisitDateTime,
                v.IPAddress,
                v.PageVisited,
                l.City,
                l.Region,
                l.Country
            FROM SiteVisitors v
            LEFT JOIN IPLocations l ON v.LocationID = l.LocationID
            LEFT JOIN IgnoredIPs i ON v.IPAddress = i.IPAddress
            WHERE i.IPAddress IS NULL
            ORDER BY v.VisitDateTime DESC
        """)
        
        visitors = []
        for row in cursor.fetchall():
            visitors.append({
                'visit_datetime': row.VisitDateTime,
                'ip_address': row.IPAddress,
                'page_visited': row.PageVisited,
                'location': {
                    'city': row.City,
                    'region': row.Region,
                    'country': row.Country
                } if row.Country else None
            })
        
        return render_template('visitors.html', visitors=visitors)
        
    except Exception as e:
        logger.error(f'Error fetching visitors: {str(e)}')
        flash('Error loading visitor data', 'error')
        return redirect(url_for('home'))
        
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/ignore_list')
@login_required
def ignore_list():
    try:
        conn = pyodbc.connect(f'DRIVER={{SQL Server}};SERVER={app.config["DB_SERVER"]};DATABASE={app.config["DB_NAME"]};UID={app.config["DB_USER"]};PWD={app.config["DB_PASSWORD"]}')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT IPAddress, DateAdded, Notes
            FROM IgnoredIPs
            ORDER BY DateAdded DESC
        """)
        
        ignored_ips = []
        for row in cursor.fetchall():
            ignored_ips.append({
                'ip_address': row.IPAddress,
                'date_added': row.DateAdded,
                'notes': row.Notes
            })
        
        return render_template('ignore_list.html', ignored_ips=ignored_ips)
        
    except Exception as e:
        logger.error(f'Error fetching ignore list: {str(e)}')
        flash('Error loading ignore list', 'error')
        return redirect(url_for('home'))
        
    finally:
        if 'conn' in locals():
            conn.close()

@csrf.exempt
@app.route('/add_to_ignore_list', methods=['POST'])
@login_required
def add_to_ignore_list():
    try:
        data = request.get_json()
        ip_address = data.get('ip_address')
        notes = data.get('notes', '')
        
        # Add debug logging
        logger.debug(f'Adding IP to ignore list: {ip_address} with notes: {notes}')
        
        conn = pyodbc.connect(f'DRIVER={{SQL Server}};SERVER={app.config["DB_SERVER"]};DATABASE={app.config["DB_NAME"]};UID={app.config["DB_USER"]};PWD={app.config["DB_PASSWORD"]}')
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO IgnoredIPs (IPAddress, Notes)
            VALUES (?, ?)
        """, (ip_address, notes))
        
        conn.commit()
        logger.debug(f'Successfully added IP {ip_address} to ignore list')
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f'Error adding to ignore list: {str(e)}')
        return jsonify({'success': False, 'error': str(e)})
        
    finally:
        if 'conn' in locals():
            conn.close()

@csrf.exempt
@app.route('/remove_from_ignore_list', methods=['POST'])
@login_required
def remove_from_ignore_list():
    try:
        logger.debug('Remove from ignore list endpoint called')
        data = request.get_json()
        logger.debug(f'Received data: {data}')
        
        if not data or 'ip_address' not in data:
            logger.error('No IP address provided in request')
            return jsonify({'success': False, 'error': 'No IP address provided'})
            
        ip_address = data['ip_address']
        logger.debug(f'Attempting to remove IP: {ip_address}')
        
        conn = pyodbc.connect(f'DRIVER={{SQL Server}};SERVER={app.config["DB_SERVER"]};DATABASE={app.config["DB_NAME"]};UID={app.config["DB_USER"]};PWD={app.config["DB_PASSWORD"]}')
        cursor = conn.cursor()
        
        # First check if IP exists
        cursor.execute("SELECT 1 FROM IgnoredIPs WHERE IPAddress = ?", (ip_address,))
        if not cursor.fetchone():
            logger.warning(f'IP {ip_address} not found in ignore list')
            return jsonify({'success': False, 'error': 'IP not found in ignore list'})
        
        # Delete the IP
        cursor.execute("DELETE FROM IgnoredIPs WHERE IPAddress = ?", (ip_address,))
        affected = cursor.rowcount
        logger.debug(f'Rows affected by delete: {affected}')
        
        conn.commit()
        logger.debug(f'Successfully removed IP {ip_address}')
        return jsonify({'success': True, 'message': f'Removed IP: {ip_address}'})
        
    except Exception as e:
        logger.error(f'Error in remove_from_ignore_list: {str(e)}')
        logger.error(f'Full traceback: {traceback.format_exc()}')
        return jsonify({'success': False, 'error': str(e)})
        
    finally:
        if 'conn' in locals():
            conn.close()

def get_or_create_location(cursor, ip_address):
    """Get existing location ID or create new one"""
    try:
        # First try to get existing location
        cursor.execute("SELECT LocationID FROM IPLocations WHERE IPAddress = ?", (ip_address,))
        existing = cursor.fetchone()
        
        if existing:
            logger.debug(f'Found existing location for IP: {ip_address}')
            return existing[0]
            
        # Skip lookup for local IPs
        if ip_address.startswith(('192.168.', '10.', '127.')):
            logger.debug('Skipping lookup for local IP')
            return None
            
        # Look up new location
        logger.debug(f'Looking up new location for IP: {ip_address}')
        response = requests.get(f'http://ip-api.com/json/{ip_address}', timeout=5)
        data = response.json()
        
        if data['status'] == 'success':
            # Insert new location
            cursor.execute("""
                INSERT INTO IPLocations (
                    IPAddress, Country, Region, City, 
                    Latitude, Longitude, ISP
                ) VALUES (?, ?, ?, ?, ?, ?, ?);
                SELECT SCOPE_IDENTITY();
                """, (
                    ip_address,
                    data.get('country', ''),
                    data.get('regionName', ''),
                    data.get('city', ''),
                    data.get('lat', 0),
                    data.get('lon', 0),
                    data.get('isp', '')
                ))
            
            new_id = cursor.fetchone()[0]
            logger.debug(f'Created new location ID {new_id} for IP: {ip_address}')
            return new_id
            
        return None
        
    except Exception as e:
        logger.error(f'Error in get_or_create_location: {str(e)}')
        return None

@app.before_request
def track_visitor():
    # Skip for static files and certain paths
    if request.path.startswith('/static') or \
       request.path in ['/favicon.ico', '/robots.txt', '/sitemap.xml']:
        return
    
    try:
        # Get real IP address from headers
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
        if ',' in ip_address:  # In case of multiple IPs, take the first one
            ip_address = ip_address.split(',')[0].strip()
            
        logger.debug(f'Tracking visitor with IP: {ip_address}')
        
        conn = pyodbc.connect(f'DRIVER={{SQL Server}};SERVER={app.config["DB_SERVER"]};DATABASE={app.config["DB_NAME"]};UID={app.config["DB_USER"]};PWD={app.config["DB_PASSWORD"]}')
        cursor = conn.cursor()
        
        # Check if IP is ignored
        cursor.execute("SELECT 1 FROM IgnoredIPs WHERE IPAddress = ?", (ip_address,))
        if cursor.fetchone():
            return
            
        # Get or create location in a single transaction
        location_id = get_or_create_location(cursor, ip_address)
        
        # Record the visit
        cursor.execute("""
            INSERT INTO SiteVisitors (
                IPAddress, PageVisited, UserAgent, LocationID
            ) VALUES (?, ?, ?, ?)
        """, (
            ip_address, 
            request.path, 
            request.user_agent.string,
            location_id  # Will be NULL if location lookup failed or wasn't attempted
        ))
        
        conn.commit()
        
    except Exception as e:
        logger.error(f'Error tracking visitor: {str(e)}')
        # Try to record visit without location if there was an error
        try:
            if 'conn' in locals():
                cursor.execute("""
                    INSERT INTO SiteVisitors (
                        IPAddress, PageVisited, UserAgent
                    ) VALUES (?, ?, ?)
                """, (ip_address, request.path, request.user_agent.string))
                conn.commit()
        except Exception as e2:
            logger.error(f'Error in fallback visitor tracking: {str(e2)}')
        
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    # Log the configuration at startup
    logger.debug('Starting application with configuration:')
    logger.debug(f'MAIL_SERVER: {app.config["MAIL_SERVER"]}')
    logger.debug(f'MAIL_PORT: {app.config["MAIL_PORT"]}')
    logger.debug(f'MAIL_USE_TLS: {app.config["MAIL_USE_TLS"]}')
    logger.debug(f'MAIL_USERNAME: {app.config["MAIL_USERNAME"]}')
    
    app.run(host='127.0.0.1', port=8091, debug=True) 