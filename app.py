import logging
import urllib.parse
import pymysql
from flask import Flask, render_template, jsonify, request
from database import get_db

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# Web Page Routes
# ---------------------------------------------------------

@app.route('/')
def customer_view():
    return render_template('index.html')


@app.route('/admin')
def admin_view():
    return render_template('admin.html')


# ---------------------------------------------------------
# RESTful API Endpoints
# ---------------------------------------------------------

@app.route('/api/tokens', methods=['POST'])
def generate_token():
    """Generates token, predicts dynamic wait time, and provides WhatsApp quick-link."""
    db = None
    cursor = None
    try:
        data = request.get_json() or {}
        customer_name = (data.get('customer_name') or 'Guest').strip() or 'Guest'

        # Phone number cleanup (Convert empty string to None for NULL DB insertion)
        raw_phone = data.get('customer_phone')
        customer_phone = raw_phone.strip() if raw_phone and str(raw_phone).strip() else None

        service_type = (data.get('service_type') or 'General Inquiry').strip() or 'General Inquiry'

        db = get_db()
        cursor = db.cursor(pymysql.cursors.DictCursor)

        # 1. Prefix by service type
        prefix = "G"
        if "Billing" in service_type: 
            prefix = "B"
        elif "Technical" in service_type: 
            prefix = "T"

        # Count tokens for daily/service sequence
        cursor.execute("SELECT COUNT(*) as count FROM tokens WHERE service_type = %s", (service_type,))
        res_count = cursor.fetchone()
        count = (res_count['count'] if res_count else 0) + 1
        token_number = f"{prefix}-{count:03d}"

        # 2. Insert into DB with explicit COMMIT
        query = """
            INSERT INTO tokens (token_number, customer_name, customer_phone, service_type, status)
            VALUES (%s, %s, %s, %s, 'waiting')
        """
        cursor.execute(query, (token_number, customer_name, customer_phone, service_type))
        token_id = cursor.lastrowid

        # VERY IMPORTANT: Commit transaction to persist in MySQL
        db.commit()

        # 3. Dynamic AI Wait Time Calculation
        cursor.execute("""
            SELECT AVG(TIMESTAMPDIFF(MINUTE, served_at, completed_at)) as avg_time 
            FROM tokens 
            WHERE service_type = %s AND status = 'completed' AND served_at IS NOT NULL
        """, (service_type,))
        avg_row = cursor.fetchone()

        avg_service_time = 5
        if avg_row and avg_row['avg_time'] is not None:
            avg_service_time = round(float(avg_row['avg_time']))

        cursor.execute("""
            SELECT COUNT(*) as ahead 
            FROM tokens 
            WHERE status = 'waiting' AND service_type = %s AND id < %s
        """, (service_type, token_id))

        ahead_row = cursor.fetchone()
        people_ahead = ahead_row['ahead'] if ahead_row else 0
        estimated_wait_minutes = people_ahead * avg_service_time

        # 4. Safe WhatsApp Link URL Encoding & Phone Cleaning
        wa_link = None
        if customer_phone:
            # Clean non-digit characters (remove +, -, spaces)
            clean_phone = ''.join(filter(str.isdigit, str(customer_phone)))

            # Default to India country code 91 if 10-digit number is entered
            if len(clean_phone) == 10:
                clean_phone = f"91{clean_phone}"

            message = f"Hello {customer_name}, your token is {token_number} for {service_type}. Approx wait time: {estimated_wait_minutes} mins."
            encoded_message = urllib.parse.quote(message)
            wa_link = f"https://api.whatsapp.com/send?phone={clean_phone}&text={encoded_message}"

        return jsonify({
            "success": True,
            "data": {
                "token_id": token_id,
                "token_number": token_number,
                "people_ahead": people_ahead,
                "estimated_wait_minutes": estimated_wait_minutes,
                "whatsapp_url": wa_link 
            }
        })

    except Exception as e:
        if db:
            db.rollback()
        logger.error(f"Token generation error: {str(e)}", exc_info=True)
        print(f"❌ Token generation error: {e}")
        return jsonify({'success': False, 'error': f'Failed to issue token: {str(e)}'}), 500
    finally:
        if cursor: 
            cursor.close()
        if db: 
            db.close()


@app.route('/api/queue-status', methods=['GET'])
def queue_status():
    """Returns live metrics, active serving details, and queue analytics."""
    db = None
    cursor = None
    try:
        db = get_db()
        cursor = db.cursor(pymysql.cursors.DictCursor)

        # Active serving token
        cursor.execute("""
            SELECT id, token_number, customer_name, service_type 
            FROM tokens WHERE status = 'serving' 
            ORDER BY served_at DESC LIMIT 1
        """)
        serving_token = cursor.fetchone()

        # Stats
        cursor.execute("SELECT COUNT(*) as waiting FROM tokens WHERE status = 'waiting'")
        waiting_count = cursor.fetchone()['waiting']

        cursor.execute("SELECT COUNT(*) as completed FROM tokens WHERE status = 'completed'")
        completed_count = cursor.fetchone()['completed']

        # Average Rating
        cursor.execute("SELECT COALESCE(AVG(rating), 5.0) as avg_rating FROM ratings")
        rating_row = cursor.fetchone()
        avg_rating = round(float(rating_row['avg_rating']), 1) if rating_row else 5.0

        return jsonify({
            'success': True,
            'data': {
                'serving_token': serving_token,
                'waiting_count': waiting_count,
                'completed_count': completed_count,
                'avg_rating': avg_rating
            }
        }), 200

    except Exception as e:
        logger.error(f"Status fetch error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': 'Database error'}), 500
    finally:
        if cursor: 
            cursor.close()
        if db: 
            db.close()


@app.route('/api/tokens/next', methods=['POST'])
def call_next():
    """Admin endpoint to call the next customer."""
    db = None
    cursor = None
    try:
        db = get_db()
        cursor = db.cursor(pymysql.cursors.DictCursor)

        # Mark current serving as completed
        cursor.execute("UPDATE tokens SET status = 'completed', completed_at = NOW() WHERE status = 'serving'")

        # Fetch next waiting token
        cursor.execute("SELECT id, token_number, customer_name, service_type FROM tokens WHERE status = 'waiting' ORDER BY id ASC LIMIT 1")
        next_token = cursor.fetchone()

        if not next_token:
            db.commit()
            return jsonify({'success': False, 'message': 'No waiting tokens in queue'}), 404

        cursor.execute("UPDATE tokens SET status = 'serving', served_at = NOW() WHERE id = %s", (next_token['id'],))
        db.commit()

        return jsonify({
            'success': True,
            'data': next_token
        }), 200

    except Exception as e:
        if db:
            db.rollback()
        logger.error(f"Call next error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': 'Server error'}), 500
    finally:
        if cursor: 
            cursor.close()
        if db: 
            db.close()


@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """Post-service feedback endpoint."""
    db = None
    cursor = None
    try:
        data = request.get_json() or {}
        token_id = data.get('token_id')
        rating = int(data.get('rating', 5))
        feedback_text = data.get('feedback_text', '').strip()

        if not token_id:
            return jsonify({'success': False, 'error': 'Token ID is required'}), 400

        db = get_db()
        cursor = db.cursor()
        cursor.execute("INSERT INTO ratings (token_id, rating, feedback_text) VALUES (%s, %s, %s)",
                       (token_id, rating, feedback_text))
        db.commit()

        return jsonify({'success': True, 'message': 'Feedback submitted successfully'}), 201

    except Exception as e:
        if db:
            db.rollback()
        logger.error(f"Feedback error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': 'Could not save feedback'}), 500
    finally:
        if cursor: 
            cursor.close()
        if db: 
            db.close()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)