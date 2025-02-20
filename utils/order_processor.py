from flask import current_app
from flask_mail import Message
import pyodbc
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def process_new_order(shipping_details, payment_details, total_amount):
    logger.debug(f'Starting order processing with: \nShipping: {shipping_details}\nPayment: {payment_details}\nTotal: {total_amount}')
    try:
        conn = pyodbc.connect('DRIVER={SQL Server};SERVER=MICROWEBSERVER\\SQLEXPRESS;DATABASE=SkyRemotes;UID=SkyAdm;PWD=Oracle69#')
        cursor = conn.cursor()
        logger.debug('Database connection established')

        # 1. Insert Customer
        customer_sql = '''
        INSERT INTO Customers (FirstName, LastName, Email, Phone, Address1, Address2, City, PostCode)
        OUTPUT INSERTED.CustomerID
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        '''
        logger.debug(f'Executing Customer SQL with values: {[
            shipping_details["firstName"],
            shipping_details["lastName"],
            shipping_details["email"],
            shipping_details["phone"],
            shipping_details["address"],
            shipping_details.get("address2", ""),
            shipping_details["city"],
            shipping_details["postcode"]
        ]}')
        
        cursor.execute(customer_sql, 
            shipping_details['firstName'],
            shipping_details['lastName'],
            shipping_details['email'],
            shipping_details['phone'],
            shipping_details['address'],
            shipping_details.get('address2', ''),
            shipping_details['city'],
            shipping_details['postcode']
        )
        customer_id = cursor.fetchval()
        logger.debug(f'Customer created with ID: {customer_id}')

        # 2. Insert Order
        order_sql = '''
        INSERT INTO Orders (CustomerID, PayPalTransactionID, PayPalStatus, TotalAmount, CurrentStatusID, Notes)
        OUTPUT INSERTED.OrderID
        VALUES (?, ?, ?, ?, 1, ?)
        '''
        logger.debug(f'Executing Order SQL with values: {[
            customer_id,
            payment_details.get("id", "TEST-PAYMENT"),
            payment_details.get("status", "COMPLETED"),
            float(total_amount),
            "Order placed via website"
        ]}')
        
        cursor.execute(order_sql,
            customer_id,
            payment_details.get('id', 'TEST-PAYMENT'),
            payment_details.get('status', 'COMPLETED'),
            float(total_amount),
            'Order placed via website'
        )
        order_id = cursor.fetchval()
        logger.debug(f'Order created with ID: {order_id}')

        # 3. Insert Order Items
        item_sql = '''
        INSERT INTO OrderItems (OrderID, ProductName, Quantity, UnitPrice, TotalPrice)
        VALUES (?, ?, ?, ?, ?)
        '''
        logger.debug(f'Executing OrderItems SQL with values: {[
            order_id,
            "Sky Remote Control",
            1,
            29.50,
            float(total_amount)
        ]}')
        
        cursor.execute(item_sql,
            order_id,
            'Sky Remote Control',
            1,
            29.50,
            float(total_amount)
        )
        logger.debug('Order items inserted')

        # 4. Insert Status History
        status_history_sql = '''
        INSERT INTO OrderStatusHistory (OrderID, StatusID, UpdatedBy, Notes)
        VALUES (?, 1, ?, ?)
        '''
        logger.debug(f'Executing Status History SQL with values: {[
            order_id,
            "System",
            "Order received and payment confirmed"
        ]}')
        
        cursor.execute(status_history_sql, 
            order_id,
            'System',
            'Order received and payment confirmed'
        )
        logger.debug('Status history inserted')

        conn.commit()
        logger.debug('Database transaction committed')

        try:
            logger.debug('Attempting to send confirmation email...')
            send_order_confirmation_email(
                shipping_details['email'],
                order_id,
                shipping_details['firstName'],
                total_amount,
                shipping_details
            )
            logger.debug('Confirmation email sent successfully')
        except Exception as email_error:
            logger.error(f'Email sending failed: {str(email_error)}')
            # Continue processing even if email fails
            # We might want to add this to a queue for retry

        return {
            'success': True,
            'order_id': order_id
        }

    except Exception as e:
        logger.error(f'Order processing error: {str(e)}')
        if 'conn' in locals():
            conn.rollback()
            logger.debug('Database transaction rolled back')
        return {
            'success': False,
            'error': str(e)
        }

    finally:
        if 'conn' in locals():
            conn.close()
            logger.debug('Database connection closed')

def send_order_confirmation_email(email, order_id, customer_name, total, shipping_details):
    from flask import render_template
    from app import mail
    
    try:
        # Create the invoice HTML
        invoice_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="text-align: center; padding: 20px;">
                <h1 style="color: #0070ba;">Sky Remotes</h1>
                <p style="color: #666;">Your source for premium Sky Remotes in the UK</p>
            </div>

            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px;">
                <h2 style="color: #28a745;">Order Confirmation</h2>
                <p>Dear {customer_name},</p>
                <p>Thank you for choosing Sky Remotes. Your order has been received and is being processed.</p>
            </div>

            <div style="margin: 20px 0; padding: 20px; border: 1px solid #dee2e6; border-radius: 5px;">
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="width: 50%; padding: 8px; vertical-align: top;">
                            <h3 style="color: #0070ba;">Billing & Shipping Address</h3>
                            <p style="margin: 0;">{shipping_details['firstName']} {shipping_details['lastName']}</p>
                            <p style="margin: 0;">{shipping_details['address']}</p>
                            {f"<p style='margin: 0;'>{shipping_details['address2']}</p>" if shipping_details.get('address2') else ""}
                            <p style="margin: 0;">{shipping_details['city']}</p>
                            <p style="margin: 0;">{shipping_details['postcode']}</p>
                            <p style="margin: 0;">Phone: {shipping_details['phone']}</p>
                            <p style="margin: 0;">Email: {shipping_details['email']}</p>
                        </td>
                        <td style="width: 50%; padding: 8px; vertical-align: top;">
                            <h3 style="color: #0070ba;">Order Information</h3>
                            <p style="margin: 0;"><strong>Order Number:</strong> #{order_id}</p>
                            <p style="margin: 0;"><strong>Order Date:</strong> {datetime.now().strftime('%d-%m-%Y %H:%M')}</p>
                        </td>
                    </tr>
                </table>
            </div>

            <div style="margin: 20px 0; padding: 20px; border: 1px solid #dee2e6; border-radius: 5px;">
                <h3 style="color: #0070ba;">Order Details</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr style="background-color: #f8f9fa;">
                        <th style="padding: 8px; border-bottom: 2px solid #dee2e6; text-align: left;">Product</th>
                        <th style="padding: 8px; border-bottom: 2px solid #dee2e6; text-align: center;">Quantity</th>
                        <th style="padding: 8px; border-bottom: 2px solid #dee2e6; text-align: right;">Unit Price</th>
                        <th style="padding: 8px; border-bottom: 2px solid #dee2e6; text-align: right;">Total</th>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">Sky Remote Control</td>
                        <td style="padding: 8px; border-bottom: 1px solid #dee2e6; text-align: center;">1</td>
                        <td style="padding: 8px; border-bottom: 1px solid #dee2e6; text-align: right;">£29.50</td>
                        <td style="padding: 8px; border-bottom: 1px solid #dee2e6; text-align: right;">£29.50</td>
                    </tr>
                    <tr>
                        <td colspan="3" style="padding: 8px; text-align: right;"><strong>Shipping:</strong></td>
                        <td style="padding: 8px; text-align: right;">FREE</td>
                    </tr>
                    <tr>
                        <td colspan="3" style="padding: 8px; text-align: right;"><strong>Total Amount:</strong></td>
                        <td style="padding: 8px; text-align: right;"><strong>£{total}</strong></td>
                    </tr>
                </table>
            </div>

            <div style="background-color: #e9ecef; padding: 20px; margin: 20px 0; border-radius: 5px;">
                <h3 style="color: #0070ba;">Delivery Information</h3>
                <ul style="list-style: none; padding: 0;">
                    <li style="margin-bottom: 10px;">✓ Same Day Dispatch for orders before 1PM</li>
                    <li style="margin-bottom: 10px;">✓ Next Day Delivery Available</li>
                    <li style="margin-bottom: 10px;">✓ Tracking Information Will Be Sent Separately</li>
                    <li>✓ All Products Tested Before Dispatch</li>
                </ul>
            </div>

            <div style="margin: 20px 0;">
                <h3 style="color: #0070ba;">Need Help?</h3>
                <p>If you have any questions about your order, please contact our customer service team:</p>
                <ul style="list-style: none; padding: 0;">
                    <li style="margin-bottom: 10px;">📞 Phone: +44 7737 463348</li>
                    <li style="margin-bottom: 10px;">📧 Email: info@skyremotes.co.uk</li>
                    <li>🕒 Business Hours: Monday - Friday, 9:00 AM - 5:00 PM</li>
                </ul>
            </div>

            <div style="text-align: center; margin-top: 30px; padding: 20px; border-top: 1px solid #dee2e6;">
                <p style="color: #666;">Thank you for shopping with Sky Remotes!</p>
                <p style="color: #666; font-size: 0.9em;">This is an automated message, please do not reply to this email.</p>
            </div>
        </div>
        """
        
        # Send customer confirmation
        customer_subject = f'Order Confirmation - Sky Remotes #{order_id}'
        customer_msg = Message(
            subject=customer_subject,
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[email]
        )
        customer_msg.html = invoice_html
        
        # Send admin notification with the same invoice
        admin_subject = f'New Order Received #{order_id}'
        admin_msg = Message(
            subject=admin_subject,
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=['info@skyremotes.co.uk']
        )
        admin_msg.html = invoice_html
        
        logger.debug('Sending customer confirmation email...')
        mail.send(customer_msg)
        logger.debug('Customer confirmation email sent')
        
        logger.debug('Sending admin notification email...')
        mail.send(admin_msg)
        logger.debug('Admin notification email sent')
        
    except Exception as e:
        logger.error(f'Failed to send emails: {str(e)}')
        raise