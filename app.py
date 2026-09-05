from flask import Flask, render_template, request, redirect, url_for, session, flash
import json, os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "school-project-secret-key"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_NAME = os.path.join(BASE_DIR, "bank_data.json")


def load_data():
    if not os.path.exists(FILE_NAME):
        return {}
    try:
        with open(FILE_NAME, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_data(accounts):
    with open(FILE_NAME, "w", encoding="utf-8") as f:
        json.dump(accounts, f, indent=4, ensure_ascii=False)


def next_account_number(accounts):
    nums = []
    for acc in accounts:
        if str(acc).startswith("ACC") and str(acc)[3:].isdigit():
            nums.append(int(str(acc)[3:]))
    return f"ACC{max(nums, default=100000) + 1}"


def add_transaction(account, kind, amount):
    account.setdefault("transactions", []).append({
        "type": kind,
        "amount": round(float(amount), 2),
        "date": datetime.now().strftime("%d-%m-%Y %I:%M %p")
    })


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/create", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        accounts = load_data()
        acc_no = next_account_number(accounts)

        name = request.form["name"].strip()
        age = int(request.form["age"])
        mobile = request.form["mobile"].strip()
        address = request.form["address"].strip()
        acc_type = request.form["account_type"]
        pin = request.form["pin"]
        initial = float(request.form["initial_deposit"])

        if age < 1 or len(pin) != 4 or not pin.isdigit() or initial < 500:
            flash("Please enter valid details. Initial deposit must be at least ₹500 and PIN must be 4 digits.", "error")
            return redirect(url_for("create"))

        accounts[acc_no] = {
            "name": name,
            "age": age,
            "mobile": mobile,
            "address": address,
            "account_type": acc_type,
            "pin": pin,
            "balance": round(initial, 2),
            "transactions": []
        }
        add_transaction(accounts[acc_no], "Account Opened", initial)
        save_data(accounts)

        return render_template("created.html", acc_no=acc_no, name=name, initial=initial)

    return render_template("create.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        accounts = load_data()
        acc_no = request.form["account_number"].strip().upper()
        pin = request.form["pin"]

        if acc_no in accounts and str(accounts[acc_no].get("pin")) == pin:
            session["account_number"] = acc_no
            return redirect(url_for("dashboard"))

        flash("Invalid account number or PIN.", "error")
    return render_template("login.html")


def logged_account():
    acc_no = session.get("account_number")
    accounts = load_data()
    if not acc_no or acc_no not in accounts:
        session.pop("account_number", None)
        return None, accounts
    return accounts[acc_no], accounts


@app.route("/dashboard")
def dashboard():
    account, _ = logged_account()
    if account is None:
        return redirect(url_for("login"))
    return render_template("dashboard.html", account=account)


@app.route("/deposit", methods=["POST"])
def deposit():
    account, accounts = logged_account()
    if account is None:
        return redirect(url_for("login"))
    amount = float(request.form["amount"])
    if amount <= 0:
        flash("Enter a valid amount.", "error")
    else:
        account["balance"] = round(account["balance"] + amount, 2)
        add_transaction(account, "Deposit", amount)
        save_data(accounts)
        flash("Money deposited successfully.", "success")
    return redirect(url_for("dashboard"))


@app.route("/withdraw", methods=["POST"])
def withdraw():
    account, accounts = logged_account()
    if account is None:
        return redirect(url_for("login"))
    amount = float(request.form["amount"])
    if amount <= 0:
        flash("Enter a valid amount.", "error")
    elif amount > account["balance"]:
        flash("Insufficient balance.", "error")
    else:
        account["balance"] = round(account["balance"] - amount, 2)
        add_transaction(account, "Withdrawal", amount)
        save_data(accounts)
        flash("Money withdrawn successfully.", "success")
    return redirect(url_for("dashboard"))


@app.route("/transactions")
def transactions():
    account, _ = logged_account()
    if account is None:
        return redirect(url_for("login"))
    return render_template("transactions.html", account=account)


@app.route("/interest", methods=["POST"])
def interest():
    account, _ = logged_account()
    if account is None:
        return redirect(url_for("login"))
    rate = float(request.form["rate"])
    years = float(request.form["years"])
    si = account["balance"] * rate * years / 100
    total = account["balance"] + si
    return render_template("interest.html", account=account, rate=rate, years=years, si=si, total=total)


@app.route("/logout")
def logout():
    session.pop("account_number", None)
    return redirect(url_for("home"))


@app.route("/search", methods=["GET", "POST"])
def search():
    result = None
    if request.method == "POST":
        accounts = load_data()
        acc_no = request.form["account_number"].strip().upper()
        result = accounts.get(acc_no)
        if result:
            result = {"account_number": acc_no, **result}
        else:
            flash("Account not found.", "error")
    return render_template("search.html", result=result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
