from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# ✅ Database Connection
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="DebugM0de_Active!",
        database="purehope"
    )

# ### ADDED #############################################################
def dict_cursor(db):
    """Return a cursor that yields rows as dictionaries."""
    return db.cursor(dictionary=True)
# #######################################################################

# ✅ Home Page
@app.route('/')
def home():
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM charities")
    charities = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('home.html', charities=charities)

# ✅ Signup
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    return render_template('signup.html')

# ✅ Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('login.html')

# ✅ Logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

# ✅ User Dashboard
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash("Please log in first!", "error")
        return redirect(url_for('login'))
    return render_template('dashboard.html')

# ✅ Charities Listing Page
@app.route('/charities')
def charities():
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM charities")
    charities = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('charities.html', charities=charities)

# ✅ Single Charity Detail View
@app.route('/charity/<int:charity_id>')
def charity_detail(charity_id):
    db = get_db_connection()
    cur = dict_cursor(db)                      #  ← uses helper (dict rows)

    # ① charity row
    cur.execute("SELECT * FROM charities WHERE id = %s", (charity_id,))
    charity = cur.fetchone()
    if not charity:
        cur.close(); db.close()
        flash("Charity not found!", "error")
        return redirect(url_for('charities'))

    # ② total raised so far
    cur.execute("SELECT COALESCE(SUM(amount),0) AS raised "
                "FROM donations WHERE charity_id = %s", (charity_id,))
    charity['funds_raised'] = cur.fetchone()['raised']
    charity['percent'] = int(
        100 * charity['funds_raised'] / charity['goal_amount']
    ) if charity['goal_amount'] else 0

    cur.close(); db.close()
    return render_template('charity_detail.html', charity=charity)

# ✅ General Donation Page
@app.route('/donate', methods=['GET', 'POST'])
def donate():
    return render_template('donate.html')

# ✅ Donate to Specific Charity
@app.route('/donate/<int:charity_id>', methods=['GET', 'POST'])
def donate_to_charity(charity_id):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM charities WHERE id = %s", (charity_id,))
    charity = cursor.fetchone()

    if not charity:
        cursor.close(); db.close()
        flash("Charity not found!", "error")
        return redirect(url_for('charities'))

    if request.method == 'POST':
        amount = request.form['amount']
        payment_method = request.form['payment_method']
        message = request.form['message']

        try:
            cursor.execute(
                "INSERT INTO donations (charity_id, amount, payment_method, message) "
                "VALUES (%s, %s, %s, %s)",
                (charity_id, amount, payment_method, message)
            )
            db.commit()

            # ### OPTIONAL: keep a cached total in charities ##############
            cursor.execute(
                "UPDATE charities SET funds_raised = funds_raised + %s "
                "WHERE id = %s", (amount, charity_id)
            )
            db.commit()
            # #############################################################

            flash(f"Your donation to {charity[1]} was successful!", "success")
            return redirect(url_for('home'))
        except Exception as e:
            db.rollback()
            flash(f"Error: {str(e)}", "error")

    cursor.close()
    db.close()
    return render_template('donate_charity.html', charity=charity)

# ✅ Database Test Route
@app.route('/test_db')
def test_db():
    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT DATABASE();")
        db_name = cursor.fetchone()
        cursor.close()
        db.close()
        return f"Connected to Database: {db_name[0]}"
    except mysql.connector.Error as err:
        return f"Database Connection Error: {err}"

# ✅ View Donation Detail by ID
@app.route('/donation/<int:donation_id>')
def donation_detail(donation_id):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("""
        SELECT d.id, c.name, d.amount, d.payment_method, d.message, d.donation_date 
        FROM donations d 
        JOIN charities c ON d.charity_id = c.id 
        WHERE d.id = %s
    """, (donation_id,))
    donation = cursor.fetchone()
    cursor.close()
    db.close()

    if not donation:
        flash("Donation not found!", "error")
        return redirect(url_for('dashboard'))

    return render_template('donation_detail.html', donation=donation)

if __name__ == '__main__':
    app.run(debug=True)
