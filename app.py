from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
import config  # Import the config file

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = config.SECRET_KEY  # Use secret key from config.py

db = SQLAlchemy(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirect unauthenticated users to login page
login_manager.session_protection = "strong"

# Many-to-Many Relationship: Expense can have multiple persons involved
expense_person_association = db.Table(
    'expense_person',
    db.Column('expense_id', db.Integer, db.ForeignKey('expense.id')),
    db.Column('person_id', db.Integer, db.ForeignKey('person.id'))
)

# Models
# Dummy admin
class AdminUser(UserMixin):
    id = 1  # Only one admin user

    def get_id(self):
        return str(self.id)

class Person(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    price = db.Column(db.Float, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    date = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(100), nullable=False)
    entire_camp = db.Column(db.Boolean, default=True)
    payed_by = db.Column(db.Integer, db.ForeignKey('person.id'))


    # Relationships
    category = db.relationship('Category')
    people = db.relationship('Person', secondary=expense_person_association, backref='expenses')

class Revenue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    person_id = db.Column(db.Integer, db.ForeignKey('person.id'))

# Initialize Database
with app.app_context():
    db.create_all()

# Function to Get by Category
def get_expenses_by_category():
    expenses = db.session.query(Category.name, db.func.sum(Expense.price)).filter(Expense.entire_camp == True).join(Expense).group_by(Category.id).all()
    categories = [row[0] for row in expenses]
    amounts = [row[1] for row in expenses]
    return categories, amounts

@app.route('/')
@login_required
def index():
    total_people = Person.query.count()

    # Sum only expenses where is_entire_camp is True
    total_expenses = db.session.query(db.func.sum(Expense.price)) \
        .filter(Expense.entire_camp == True) \
        .scalar() or 0

    per_person_cost = total_expenses / total_people if total_people > 0 else 0
    categories, amounts = get_expenses_by_category()

    return render_template(
        'index.html',
        total_people=total_people,
        total_expenses=total_expenses,
        per_person_cost=per_person_cost,
        categories=categories,
        amounts=amounts
    )

@login_manager.user_loader
def load_user(user_id):
    if user_id == "1":  # Only allow the admin user
        return AdminUser()  # Return an instance of AdminUser
    return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check credentials from config.py
        if username == config.ADMIN_USERNAME and password == config.ADMIN_PASSWORD:
            admin = AdminUser()
            login_user(admin)
            session.permanent = True  # Ensure session persists
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials', 'danger')

    return render_template('login.html')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# --------------- Manage People ---------------
@app.route('/people', methods=['GET', 'POST'])
@login_required
def manage_people():
    if request.method == 'POST':
        name = request.form['name']
        new_person = Person(name=name)
        db.session.add(new_person)
        db.session.commit()
        flash('{%s} added successfully!' % name, 'success')  # Green success toast
    people = Person.query.all()
    return render_template('people.html', people=people)


@app.route('/delete_person/<int:id>')
@login_required
def delete_person(id):
    person = Person.query.get(id)
    db.session.delete(person)
    db.session.commit()
    return redirect(url_for('manage_people'))

# --------------- Manage Categories ---------------
@app.route('/categories', methods=['GET', 'POST'])
@login_required
def manage_categories():
    if request.method == 'POST':
        name = request.form['name']
        if name:
            new_category = Category(name=name)
            db.session.add(new_category)
            db.session.commit()
    categories = Category.query.all()
    return render_template('categories.html', categories=categories)

@app.route('/delete_category/<int:id>')
@login_required
def delete_category(id):
    category = Category.query.get(id)
    db.session.delete(category)
    db.session.commit()
    return redirect(url_for('manage_categories'))

# --------------- Manage Expenses ---------------
@app.route('/expenses', methods=['GET', 'POST'])
@login_required
def manage_expenses():
    people = Person.query.all()
    categories = Category.query.all()

    if request.method == 'POST':
        description = request.form['description']
        price = request.form['price']
        category_id = request.form['category']
        date = request.form['date']
        payed_by = request.form['payed_by']
        entire_camp = request.form.get('entire_camp') == 'on'
        selected_people_ids = request.form.getlist('people')

        new_expense = Expense(
            price=price, 
            category_id=category_id, 
            date=date, 
            description=description, 
            entire_camp=entire_camp,
            payed_by=payed_by
        )

        if not entire_camp:
            new_expense.people = Person.query.filter(Person.id.in_(selected_people_ids)).all()

        db.session.add(new_expense)
        db.session.commit()
        return redirect(url_for('manage_expenses'))

    expenses = db.session.query(
        Expense.id,
        Expense.description,
        Expense.price,
        Expense.date,
        Expense.entire_camp,
        Expense.payed_by,
        Category.name.label('category_name')
    ).join(Category).all()

    expense_data = []
    for exp in expenses:
        involved_people = db.session.query(Person.name).join(expense_person_association).filter(expense_person_association.c.expense_id == exp.id).all()
        involved_people_names = [p.name for p in involved_people]
        audience = "Entire Camp" if exp.entire_camp else ", ".join(involved_people_names)
        payed_by_name = db.session.query(Person.name).filter(Person.id == exp.payed_by).scalar()
        expense_data.append({
            "id": exp.id,
            "description": exp.description,
            "price": exp.price,
            "date": exp.date,
            "category_name": exp.category_name,
            "audience": audience,
            "payed_by": payed_by_name if payed_by_name else ""
        })

    return render_template('expenses.html', expenses=expense_data, people=people, categories=categories)

@app.route('/delete_expense/<int:id>')
@login_required
def delete_expense(id):
    expense = Expense.query.get(id)
    db.session.delete(expense)
    db.session.commit()
    return redirect(url_for('manage_expenses'))

@app.route('/update_expense', methods=['POST'])
@login_required
def update_expense():
    expense_id = request.form.get("id")
    expense = Expense.query.get(expense_id)

    if not expense:
        return jsonify({"success": False, "message": "Expense not found"}), 404

    try:
        # Update basic fields
        expense.description = request.form["description"]
        expense.price = float(request.form["price"])
        expense.category_id = int(request.form["category"])
        expense.date = request.form["date"]
        # expense.payed_by = int(request.form["payed_by"])
        # expense.entire_camp = request.form.get("entire_camp") == "on"

        # Update people associated with the expense if it's not for the entire camp
        if not expense.entire_camp:
            selected_people_ids = request.form.getlist("people")
            expense.people = Person.query.filter(Person.id.in_(selected_people_ids)).all()
        else:
            expense.people = []  # Clear any individual assignments


        # Commit changes
        db.session.commit()
        return jsonify({"success": True, "message": "Expense updated successfully"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    
# --------------- Manage Payments (Revenues) ---------------
@app.route('/revenues', methods=['GET', 'POST'])
@login_required
def manage_revenues():
    people = Person.query.all()
    if request.method == 'POST':
        amount = request.form['amount']
        person_id = request.form['person']
        new_revenue = Revenue(amount=amount, person_id=person_id)
        db.session.add(new_revenue)
        db.session.commit()
    revenues = db.session.query(
        Revenue.id,
        Revenue.amount,
        Person.name.label("person_name")
    ).join(Person, Revenue.person_id == Person.id).all()
    return render_template('revenues.html', revenues=revenues, people=people)

@app.route('/delete_revenue/<int:id>')
@login_required
def delete_revenue(id):
    revenue = Revenue.query.get(id)
    db.session.delete(revenue)
    db.session.commit()
    return redirect(url_for('manage_revenues'))

# --------------- View Balance ---------------
@app.route('/balance')
@login_required
def balance():
    people = Person.query.all()
    balances = []
    total_people = Person.query.count()

    # Get the total expenses that are marked as "entire camp"
    total_expenses = db.session.query(db.func.sum(Expense.price)) \
        .filter(Expense.entire_camp == True).scalar() or 0
    per_person_cost = total_expenses / total_people if total_people > 0 else 0

    for person in people:
        # Amount this person paid for expenses
        payed = db.session.query(db.func.sum(Expense.price)) \
            .filter(Expense.payed_by == person.id).scalar() or 0

        # Get all expenses linked to this person
        expenses = db.session.query(Expense.id, Expense.price) \
            .join(expense_person_association) \
            .filter(expense_person_association.c.person_id == person.id).all()

        total_cost_personal = 0

        # Calculate the per-person share for each expense
        for expense_id, expense_price in expenses:
            # Count how many people are linked to this expense
            num_people = db.session.query(db.func.count(expense_person_association.c.person_id)) \
                .filter(expense_person_association.c.expense_id == expense_id).scalar() or 1
            
            # Add the proportional part of the expense
            total_cost_personal += expense_price / num_people

        # Get the total amount the person has paid
        total_paid = db.session.query(db.func.sum(Revenue.amount)) \
            .filter_by(person_id=person.id).scalar() or 0

        # Calculate the final balance
        balance = round(total_paid + payed - total_cost_personal - per_person_cost)

        balances.append({'name': person.name, 'balance': balance})

    return render_template('balance.html', balances=balances)

# --------------- Export Expenses ---------------
@app.route('/export_expenses')
@login_required
def export_expenses():
    expenses = Expense.query.all()

    def generate():
        data = [["ID", "Amount", "Category", "Audience", "Date"]]
        for expense in expenses:
            category = Category.query.get(expense.category_id).name
            audience = "Entire Camp" if expense.entire_camp else ", ".join([p.name for p in expense.people])
            data.append([expense.id, expense.price, category, audience, expense.date])

        output = []
        for row in data:
            output.append(",".join(map(str, row)))
        return "\n".join(output)

    response = Response(generate(), mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=expenses.csv"
    return response

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)