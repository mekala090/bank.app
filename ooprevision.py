"""Streamlit banking simulator using the OOP model in bank.py."""

import streamlit as st

from bank import Customer, InsufficientFundsError, SavingsAccount


st.set_page_config(page_title="OOP Banking Simulator", page_icon="🏦", layout="wide")


def get_customer_data():
    if "customer_data" not in st.session_state:
        st.session_state.customer_data = {}
    return st.session_state.customer_data


def get_account_records():
    return [
        (customer_id, account)
        for customer_id, customer in get_customer_data().items()
        for account in customer["accounts"]
    ]


def account_label(account):
    account_type = account["kind"].title()
    return f"#{account['account_no']} · {account['owner']} · {account_type}"


def get_next_id(key, existing_ids, first_id):
    if key not in st.session_state:
        st.session_state[key] = max(existing_ids, default=first_id - 1) + 1
    return st.session_state[key]


def serialize_account(account):
    return {
        "account_no": account.account_no,
        "owner": account.owner.name,
        "kind": "savings" if isinstance(account, SavingsAccount) else "current",
        "balance": account.balance,
        "interest_rate": (
            account.interest_rate if isinstance(account, SavingsAccount) else None
        ),
        "min_balance": (
            account.min_balance if isinstance(account, SavingsAccount) else None
        ),
        "transactions": [list(transaction) for transaction in account.transactions],
    }


def restore_account(customer_id, account_data):
    owner = Customer(account_data["owner"])
    owner.customer_id = customer_id
    options = {}
    if account_data["kind"] == "savings":
        options = {
            "interest_rate": account_data["interest_rate"],
            "min_balance": account_data["min_balance"],
        }
    account = owner.open_account(
        account_data["kind"],
        account_data["balance"],
        **options,
    )
    account.account_no = account_data["account_no"]
    account.transactions = [
        tuple(transaction) for transaction in account_data["transactions"]
    ]
    return account


def save_account(customer_id, account):
    customers = get_customer_data()
    customer = dict(customers[customer_id])
    updated = serialize_account(account)
    customer["accounts"] = [
        updated if item["account_no"] == account.account_no else item
        for item in customer["accounts"]
    ]
    customers = dict(customers)
    customers[customer_id] = customer
    st.session_state["customer_data"] = customers


def render_dashboard():
    customers = get_customer_data()
    account_records = get_account_records()
    total_balance = sum(
        account["balance"] for _, account in account_records
    )

    st.subheader("Overview")
    customer_col, account_col, balance_col = st.columns(3)
    customer_col.metric("Customers", len(customers))
    account_col.metric("Accounts", len(account_records))
    balance_col.metric("Total deposits", f"INR {total_balance:,.2f}")

    if account_records:
        st.dataframe(
            [
                {
                    "Account": account["account_no"],
                    "Customer": account["owner"],
                    "Type": account["kind"].title(),
                    "Balance": f"INR {account['balance']:,.2f}",
                }
                for _, account in account_records
            ],
            hide_index=True,
            width="stretch",
        )
    else:
        st.info("No accounts yet. Create a customer, then open an account.")


def render_customers_and_accounts():
    customers = get_customer_data()
    create_tab, account_tab = st.tabs(["Create customer", "Open account"])

    with create_tab:
        with st.form("create_customer_form", clear_on_submit=True):
            name = st.text_input("Customer name")
            submitted = st.form_submit_button("Create customer", type="primary")
        if submitted:
            try:
                customer = Customer(name)
                customer_id = get_next_id(
                    "next_customer_id", customers.keys(), first_id=1
                )
                customer.customer_id = customer_id
                customers = dict(customers)
                customers[customer_id] = {"name": customer.name, "accounts": []}
                st.session_state["customer_data"] = customers
                st.session_state["next_customer_id"] = customer_id + 1
                st.success(f"Created customer #{customer_id}: {customer.name}")
            except ValueError as error:
                st.error(str(error))

    with account_tab:
        if not customers:
            st.info("Create a customer before opening an account.")
            return

        with st.form("open_account_form", clear_on_submit=True):
            customer_id = st.selectbox(
                "Customer",
                list(customers),
                format_func=lambda value: f"#{value} · {customers[value]['name']}",
            )
            kind = st.selectbox("Account type", ["current", "savings"])
            opening_balance = st.number_input(
                "Opening balance (INR)",
                min_value=0.0,
                step=100.0,
                format="%.2f",
            )
            submitted = st.form_submit_button("Open account", type="primary")
        if submitted:
            try:
                record = dict(customers[customer_id])
                owner = Customer(record["name"])
                owner.customer_id = customer_id
                account = owner.open_account(kind, opening_balance)
                existing_ids = [
                    item["account_no"]
                    for _, item in get_account_records()
                ]
                account_no = get_next_id(
                    "next_account_no", existing_ids, first_id=1001
                )
                account.account_no = account_no
                record["accounts"] = [
                    *record["accounts"],
                    serialize_account(account),
                ]
                customers = dict(customers)
                customers[customer_id] = record
                st.session_state["customer_data"] = customers
                st.session_state["next_account_no"] = account_no + 1
                st.success(
                    f"Opened {type(account).__name__} #{account_no} "
                    f"for {owner.name}."
                )
            except ValueError as error:
                st.error(str(error))


def render_transactions():
    account_records = get_account_records()
    accounts_by_number = {
        account["account_no"]: (customer_id, account)
        for customer_id, account in account_records
    }
    if not accounts_by_number:
        st.info("Open an account before making transactions.")
        return

    account_numbers = list(accounts_by_number)
    label = lambda number: account_label(accounts_by_number[number][1])
    deposit_tab, withdrawal_tab, transfer_tab, interest_tab = st.tabs(
        ["Deposit", "Withdraw", "Transfer", "Savings interest"]
    )

    with deposit_tab:
        with st.form("deposit_form", clear_on_submit=True):
            account_no = st.selectbox(
                "Deposit into", account_numbers, format_func=label
            )
            amount = st.number_input(
                "Amount (INR)",
                min_value=0.0,
                step=100.0,
                format="%.2f",
                key="deposit_amount",
            )
            submitted = st.form_submit_button("Deposit", type="primary")
        if submitted:
            customer_id, account_data = accounts_by_number[account_no]
            try:
                account = restore_account(customer_id, account_data)
                account.deposit(amount)
                save_account(customer_id, account)
                st.success(f"Deposit complete. New balance: INR {account.balance:,.2f}")
            except ValueError as error:
                st.error(str(error))

    with withdrawal_tab:
        with st.form("withdrawal_form", clear_on_submit=True):
            account_no = st.selectbox(
                "Withdraw from", account_numbers, format_func=label
            )
            amount = st.number_input(
                "Amount (INR)",
                min_value=0.0,
                step=100.0,
                format="%.2f",
                key="withdrawal_amount",
            )
            submitted = st.form_submit_button("Withdraw", type="primary")
        if submitted:
            customer_id, account_data = accounts_by_number[account_no]
            try:
                account = restore_account(customer_id, account_data)
                account.withdraw(amount)
                save_account(customer_id, account)
                st.success(
                    f"Withdrawal complete. New balance: INR {account.balance:,.2f}"
                )
            except (InsufficientFundsError, ValueError) as error:
                st.error(str(error))

    with transfer_tab:
        with st.form("transfer_form", clear_on_submit=True):
            source_no = st.selectbox(
                "From account", account_numbers, format_func=label
            )
            destination_numbers = [
                number for number in account_numbers if number != source_no
            ]
            if destination_numbers:
                target_no = st.selectbox(
                    "To account", destination_numbers, format_func=label
                )
                amount = st.number_input(
                    "Amount (INR)",
                    min_value=0.0,
                    step=100.0,
                    format="%.2f",
                    key="transfer_amount",
                )
                submitted = st.form_submit_button("Transfer", type="primary")
            else:
                st.info("A transfer requires at least two accounts.")
                target_no = None
                amount = 0.0
                submitted = False
        if submitted and target_no is not None:
            source_customer_id, source_data = accounts_by_number[source_no]
            target_customer_id, target_data = accounts_by_number[target_no]
            try:
                source = restore_account(source_customer_id, source_data)
                target = restore_account(target_customer_id, target_data)
                source.transfer(target, amount)
                save_account(source_customer_id, source)
                save_account(target_customer_id, target)
                st.success(
                    f"Transferred INR {amount:,.2f}. "
                    f"Source balance: INR {source.balance:,.2f}; "
                    f"recipient balance: INR {target.balance:,.2f}."
                )
            except (InsufficientFundsError, ValueError) as error:
                st.error(str(error))

    with interest_tab:
        savings_numbers = [
            number
            for number, (_, account) in accounts_by_number.items()
            if account["kind"] == "savings"
        ]
        if not savings_numbers:
            st.info("Open a savings account before adding interest.")
        else:
            with st.form("interest_form"):
                account_no = st.selectbox(
                    "Savings account", savings_numbers, format_func=label
                )
                submitted = st.form_submit_button("Add monthly interest")
            if submitted:
                customer_id, account_data = accounts_by_number[account_no]
                account = restore_account(customer_id, account_data)
                balance = account.add_interest()
                save_account(customer_id, account)
                st.success(f"Interest applied. New balance: INR {balance:,.2f}")


def render_statements():
    account_records = get_account_records()
    if not account_records:
        st.info("Open an account to view its transaction statement.")
        return

    accounts_by_number = {
        account["account_no"]: account for _, account in account_records
    }
    account_no = st.selectbox(
        "Select account",
        list(accounts_by_number),
        format_func=lambda number: account_label(accounts_by_number[number]),
        key="statement_account",
    )
    transactions = accounts_by_number[account_no]["transactions"]
    st.dataframe(
        [
            {
                "Date and time": timestamp,
                "Transaction": kind,
                "Amount": f"INR {amount:,.2f}",
                "Balance": f"INR {balance:,.2f}",
            }
            for timestamp, kind, amount, balance in transactions
        ],
        hide_index=True,
        width="stretch",
    )


def main():
    st.title("🏦 OOP Banking Simulator")
    st.caption(
        "Manage customers and accounts, and see transaction balances update live. "
        "Demo data is stored in this browser session only."
    )

    page = st.sidebar.radio(
        "Banking",
        ["Dashboard", "Customers & accounts", "Transactions", "Statements"],
    )

    if page == "Dashboard":
        render_dashboard()
    elif page == "Customers & accounts":
        render_customers_and_accounts()
    elif page == "Transactions":
        render_transactions()
    else:
        render_statements()


main()
