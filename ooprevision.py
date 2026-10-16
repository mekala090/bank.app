"""Streamlit banking simulator using the OOP model in bank.py."""

import streamlit as st

from bank import (
    Account,
    Customer,
    InsufficientFundsError,
    SavingsAccount,
)


st.set_page_config(page_title="OOP Banking Simulator", page_icon="🏦", layout="wide")


def get_customers() -> dict[int, Customer]:
    records = st.session_state.get("customer_data", {})
    customers = {}
    for customer_id, record in records.items():
        customer = Customer(record["name"])
        customer.customer_id = customer_id
        for saved_account in record["accounts"]:
            kind = saved_account["kind"]
            options = {}
            if kind == "savings":
                options = {
                    "interest_rate": saved_account["interest_rate"],
                    "min_balance": saved_account["min_balance"],
                }
            account = customer.open_account(
                kind,
                saved_account["balance"],
                **options,
            )
            account.account_no = saved_account["account_no"]
            account.transactions = [
                tuple(transaction)
                for transaction in saved_account["transactions"]
            ]
        customers[customer_id] = customer
    return customers


def save_customers(customers: dict[int, Customer]) -> None:
    st.session_state["customer_data"] = {
        customer_id: {
            "name": customer.name,
            "accounts": [
                {
                    "account_no": account.account_no,
                    "kind": (
                        "savings"
                        if isinstance(account, SavingsAccount)
                        else "current"
                    ),
                    "balance": account.balance,
                    "interest_rate": (
                        account.interest_rate
                        if isinstance(account, SavingsAccount)
                        else None
                    ),
                    "min_balance": (
                        account.min_balance
                        if isinstance(account, SavingsAccount)
                        else None
                    ),
                    "transactions": [
                        list(transaction) for transaction in account.transactions
                    ],
                }
                for account in customer.accounts
            ],
        }
        for customer_id, customer in customers.items()
    }


def get_accounts(customers: dict[int, Customer]) -> list[Account]:
    return [
        account
        for customer in customers.values()
        for account in customer.accounts
    ]


def account_label(account: Account) -> str:
    return (
        f"#{account.account_no} · {account.owner.name} · "
        f"{type(account).__name__.replace('Account', '') or 'Current'}"
    )


def account_table(accounts: list[Account]) -> list[dict[str, str]]:
    return [
        {
            "Account": str(account.account_no),
            "Customer": account.owner.name,
            "Type": type(account).__name__.replace("Account", "") or "Current",
            "Balance": f"INR {account.balance:,.2f}",
        }
        for account in accounts
    ]


def render_dashboard():
    customers = get_customers()
    accounts = get_accounts(customers)
    total_balance = sum(account.balance for account in accounts)

    st.subheader("Overview")
    col1, col2, col3 = st.columns(3)
    col1.metric("Customers", len(customers))
    col2.metric("Accounts", len(accounts))
    col3.metric("Total deposits", f"INR {total_balance:,.2f}")

    if accounts:
        st.dataframe(account_table(accounts), hide_index=True, width="stretch")
    else:
        st.info("No accounts yet. Create a customer, then open an account.")


def render_customers_and_accounts():
    customers = get_customers()
    create_tab, account_tab = st.tabs(["Create customer", "Open account"])

    with create_tab:
        with st.form("create_customer_form", clear_on_submit=True):
            name = st.text_input("Customer name")
            submitted = st.form_submit_button("Create customer", type="primary")
        if submitted:
            try:
                customer = Customer(name)
                customers[customer.customer_id] = customer
                save_customers(customers)
                st.success(
                    f"Created customer #{customer.customer_id}: {customer.name}"
                )
            except ValueError as error:
                st.error(str(error))

    with account_tab:
        if not customers:
            st.info("Create a customer before opening an account.")
            return

        customer_ids = list(customers)
        with st.form("open_account_form", clear_on_submit=True):
            customer_id = st.selectbox(
                "Customer",
                customer_ids,
                format_func=lambda value: (
                    f"#{value} · {customers[value].name}"
                ),
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
                account = customers[customer_id].open_account(kind, opening_balance)
                save_customers(customers)
                st.success(
                    f"Opened {type(account).__name__} #{account.account_no} "
                    f"for {account.owner.name}."
                )
            except ValueError as error:
                st.error(str(error))


def render_transactions():
    customers = get_customers()
    accounts = get_accounts(customers)
    if not accounts:
        st.info("Open an account before making transactions.")
        return
    accounts_by_number = {account.account_no: account for account in accounts}

    deposit_tab, withdrawal_tab, transfer_tab, interest_tab = st.tabs(
        ["Deposit", "Withdraw", "Transfer", "Savings interest"]
    )

    with deposit_tab:
        with st.form("deposit_form", clear_on_submit=True):
            account_no = st.selectbox(
                "Deposit into",
                list(accounts_by_number),
                format_func=lambda number: account_label(accounts_by_number[number]),
            )
            amount = st.number_input(
                "Amount (INR)", min_value=0.0, step=100.0, format="%.2f",
                key="deposit_amount",
            )
            submitted = st.form_submit_button("Deposit", type="primary")
        if submitted:
            account = accounts_by_number[account_no]
            try:
                account.deposit(amount)
                save_customers(customers)
                st.success(f"Deposit complete. New balance: INR {account.balance:,.2f}")
            except ValueError as error:
                st.error(str(error))

    with withdrawal_tab:
        with st.form("withdrawal_form", clear_on_submit=True):
            account_no = st.selectbox(
                "Withdraw from",
                list(accounts_by_number),
                format_func=lambda number: account_label(accounts_by_number[number]),
            )
            amount = st.number_input(
                "Amount (INR)", min_value=0.0, step=100.0, format="%.2f",
                key="withdrawal_amount",
            )
            submitted = st.form_submit_button("Withdraw", type="primary")
        if submitted:
            account = accounts_by_number[account_no]
            try:
                account.withdraw(amount)
                save_customers(customers)
                st.success(
                    f"Withdrawal complete. New balance: INR {account.balance:,.2f}"
                )
            except (InsufficientFundsError, ValueError) as error:
                st.error(str(error))

    with transfer_tab:
        with st.form("transfer_form", clear_on_submit=True):
            source_no = st.selectbox(
                "From account",
                list(accounts_by_number),
                format_func=lambda number: account_label(accounts_by_number[number]),
            )
            destination_numbers = [
                number for number in accounts_by_number if number != source_no
            ]
            if destination_numbers:
                target_no = st.selectbox(
                    "To account",
                    destination_numbers,
                    format_func=lambda number: account_label(accounts_by_number[number]),
                )
                amount = st.number_input(
                    "Amount (INR)", min_value=0.0, step=100.0, format="%.2f",
                    key="transfer_amount",
                )
                submitted = st.form_submit_button("Transfer", type="primary")
            else:
                st.info("A transfer requires at least two accounts.")
                submitted = False
                target_no = None
                amount = 0.0
        if submitted and target_no is not None:
            source = accounts_by_number[source_no]
            target = accounts_by_number[target_no]
            try:
                source.transfer(target, amount)
                save_customers(customers)
                st.success(
                    f"Transferred INR {amount:,.2f}. "
                    f"Source balance: INR {source.balance:,.2f}; "
                    f"recipient balance: INR {target.balance:,.2f}."
                )
            except (InsufficientFundsError, ValueError) as error:
                st.error(str(error))

    with interest_tab:
        savings_account_numbers = [
            number
            for number, account in accounts_by_number.items()
            if isinstance(account, SavingsAccount)
        ]
        if not savings_account_numbers:
            st.info("Open a savings account before adding interest.")
        else:
            with st.form("interest_form"):
                account_no = st.selectbox(
                    "Savings account",
                    savings_account_numbers,
                    format_func=lambda number: account_label(accounts_by_number[number]),
                )
                submitted = st.form_submit_button("Add monthly interest")
            if submitted:
                account = accounts_by_number[account_no]
                balance = account.add_interest()
                save_customers(customers)
                st.success(f"Interest applied. New balance: INR {balance:,.2f}")


def render_statements():
    customers = get_customers()
    accounts = get_accounts(customers)
    if not accounts:
        st.info("Open an account to view its transaction statement.")
        return

    accounts_by_number = {account.account_no: account for account in accounts}
    account_no = st.selectbox(
        "Select account",
        list(accounts_by_number),
        format_func=lambda number: account_label(accounts_by_number[number]),
        key="statement_account",
    )
    account = accounts_by_number[account_no]
    transactions = [
        {
            "Date and time": timestamp,
            "Transaction": kind,
            "Amount": f"INR {amount:,.2f}",
            "Balance": f"INR {balance:,.2f}",
        }
        for timestamp, kind, amount, balance in account.transactions
    ]
    st.dataframe(transactions, hide_index=True, width="stretch")


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
