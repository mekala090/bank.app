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
    if "customers" not in st.session_state:
        st.session_state.customers = {}
    return st.session_state.customers


def save_customers(customers: dict[int, Customer]) -> None:
    st.session_state.customers = dict(customers)


def get_accounts() -> list[Account]:
    return [
        account
        for customer in get_customers().values()
        for account in customer.accounts
    ]


def account_label(account: Account) -> str:
    return (
        f"#{account.account_no} · {account.owner.name} · "
        f"INR {account.balance:,.2f}"
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
    accounts = get_accounts()
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
    accounts = get_accounts()
    if not accounts:
        st.info("Open an account before making transactions.")
        return

    deposit_tab, withdrawal_tab, transfer_tab, interest_tab = st.tabs(
        ["Deposit", "Withdraw", "Transfer", "Savings interest"]
    )

    with deposit_tab:
        with st.form("deposit_form", clear_on_submit=True):
            account = st.selectbox(
                "Deposit into", accounts, format_func=account_label
            )
            amount = st.number_input(
                "Amount (INR)", min_value=0.0, step=100.0, format="%.2f",
                key="deposit_amount",
            )
            submitted = st.form_submit_button("Deposit", type="primary")
        if submitted:
            try:
                account.deposit(amount)
                save_customers(get_customers())
                st.success(f"Deposit complete. New balance: INR {account.balance:,.2f}")
            except ValueError as error:
                st.error(str(error))

    with withdrawal_tab:
        with st.form("withdrawal_form", clear_on_submit=True):
            account = st.selectbox(
                "Withdraw from", accounts, format_func=account_label
            )
            amount = st.number_input(
                "Amount (INR)", min_value=0.0, step=100.0, format="%.2f",
                key="withdrawal_amount",
            )
            submitted = st.form_submit_button("Withdraw", type="primary")
        if submitted:
            try:
                account.withdraw(amount)
                save_customers(get_customers())
                st.success(
                    f"Withdrawal complete. New balance: INR {account.balance:,.2f}"
                )
            except (InsufficientFundsError, ValueError) as error:
                st.error(str(error))

    with transfer_tab:
        with st.form("transfer_form", clear_on_submit=True):
            source = st.selectbox(
                "From account", accounts, format_func=account_label
            )
            destinations = [account for account in accounts if account is not source]
            if destinations:
                target = st.selectbox(
                    "To account", destinations, format_func=account_label
                )
                amount = st.number_input(
                    "Amount (INR)", min_value=0.0, step=100.0, format="%.2f",
                    key="transfer_amount",
                )
                submitted = st.form_submit_button("Transfer", type="primary")
            else:
                st.info("A transfer requires at least two accounts.")
                submitted = False
                target = None
                amount = 0.0
        if submitted and target is not None:
            try:
                source.transfer(target, amount)
                save_customers(get_customers())
                st.success(
                    f"Transferred INR {amount:,.2f}. "
                    f"Source balance: INR {source.balance:,.2f}; "
                    f"recipient balance: INR {target.balance:,.2f}."
                )
            except (InsufficientFundsError, ValueError) as error:
                st.error(str(error))

    with interest_tab:
        savings_accounts = [
            account for account in accounts if isinstance(account, SavingsAccount)
        ]
        if not savings_accounts:
            st.info("Open a savings account before adding interest.")
        else:
            with st.form("interest_form"):
                account = st.selectbox(
                    "Savings account",
                    savings_accounts,
                    format_func=account_label,
                )
                submitted = st.form_submit_button("Add monthly interest")
            if submitted:
                balance = account.add_interest()
                save_customers(get_customers())
                st.success(f"Interest applied. New balance: INR {balance:,.2f}")


def render_statements():
    accounts = get_accounts()
    if not accounts:
        st.info("Open an account to view its transaction statement.")
        return

    account = st.selectbox(
        "Select account", accounts, format_func=account_label, key="statement_account"
    )
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
