Here’s a README.md file for your project:

Expense Tracker Web App

This is a Flask-based Expense Tracker web application that allows managing expenses, categories, people, and payments. It includes authentication with a single admin user, whose credentials are stored in a config file.

🚀 Features

✅ Secure Login – Only an admin can log in (credentials in config.py).
✅ Manage People – Add and delete participants.
✅ Manage Expenses – Add, edit, and delete expenses with categories.
✅ Expense Sharing – Expenses can be for entire camp or specific people.
✅ Manage Categories – Create and remove categories.
✅ Record Payments – Track revenue payments from participants.
✅ Balance Calculation – Calculates how much each person owes or is owed.
✅ Data Export – Download expenses as a CSV file.
✅ Session Security – Uses Flask-Login to enforce login requirements.

📌 Installation

1️⃣ Clone the Repository

3️⃣ Install Dependencies

pip install -r requirements.txt

4️⃣ Configure Admin Credentials

Edit the config.py file and set the admin username & password:

SECRET_KEY = "your_secret_key"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "your_password"

5️⃣ Run the Application

python app.py

Access the app in your browser at http://localhost:2020.

🛠 Tech Stack

	•	Flask (Backend)
	•	Flask-SQLAlchemy (Database ORM)
	•	Flask-Login (User Authentication)
	•	SQLite (Database)
	•	Bootstrap 5 (Frontend Styling)

📄 License

This project is licensed under the MIT License.

Let me know if you want any modifications! 🚀
