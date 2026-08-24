import os
from flask import Flask, render_template, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Secret key for flash messages
app.secret_key = os.environ.get(
    "SECRET_KEY",
    "expense-tracker-secret-key"
)

# Database configuration
database_url = os.environ.get("DATABASE_URL", "sqlite:///expenses.db")

# Render/PostgreSQL compatibility
if database_url.startswith("postgres://"):
    database_url = database_url.replace(
        "postgres://", "postgresql://", 1
    )

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# Expense Model
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.String(20), nullable=False)


# Home / Expense List
@app.route("/")
def index():

    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()

    query = Expense.query

    if search:
        query = query.filter(
            Expense.title.ilike(f"%{search}%")
        )

    if category:
        query = query.filter_by(category=category)

    expenses = query.order_by(Expense.date.desc()).all()

    total = sum(expense.amount for expense in expenses)

    categories = [
        "Food",
        "Travel",
        "Shopping",
        "Bills",
        "Education",
        "Health",
        "Other"
    ]

    return render_template(
        "index.html",
        expenses=expenses,
        total=total,
        categories=categories,
        search=search,
        selected_category=category
    )


# Add Expense
@app.route("/add", methods=["GET", "POST"])
def add_expense():

    if request.method == "POST":

        title = request.form["title"].strip()
        category = request.form["category"].strip()
        amount = request.form["amount"].strip()
        date = request.form["date"].strip()

        # Validation
        if not title or not category or not amount or not date:
            flash("Please fill all fields.", "danger")
            return redirect("/add")

        try:
            amount = float(amount)
        except ValueError:
            flash("Amount must be a number.", "danger")
            return redirect("/add")

        if amount <= 0:
            flash("Amount must be greater than 0.", "danger")
            return redirect("/add")

        expense = Expense(
            title=title,
            category=category,
            amount=amount,
            date=date
        )

        db.session.add(expense)
        db.session.commit()

        flash("Expense added successfully!", "success")

        return redirect("/")

    return render_template("add.html")


# Update Expense
@app.route("/update/<int:id>", methods=["GET", "POST"])
def update_expense(id):

    expense = Expense.query.get_or_404(id)

    if request.method == "POST":

        title = request.form["title"].strip()
        category = request.form["category"].strip()
        amount = request.form["amount"].strip()
        date = request.form["date"].strip()

        if not title or not category or not amount or not date:
            flash("Please fill all fields.", "danger")
            return redirect(f"/update/{id}")

        try:
            amount = float(amount)
        except ValueError:
            flash("Amount must be a number.", "danger")
            return redirect(f"/update/{id}")

        if amount <= 0:
            flash("Amount must be greater than 0.", "danger")
            return redirect(f"/update/{id}")

        expense.title = title
        expense.category = category
        expense.amount = amount
        expense.date = date

        db.session.commit()

        flash("Expense updated successfully!", "success")

        return redirect("/")

    return render_template(
        "update.html",
        expense=expense
    )


# Delete Expense
@app.route("/delete/<int:id>")
def delete_expense(id):

    expense = Expense.query.get_or_404(id)

    db.session.delete(expense)
    db.session.commit()

    flash("Expense deleted successfully!", "success")

    return redirect("/")


# Create database tables
with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=True
    )