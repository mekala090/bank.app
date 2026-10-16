import itertools
from datetime import datetime


class InsufficientFundsError(Exception):
    """Raised when a withdrawal/transfer exceeds the available balance."""


class InvalidAmountError(ValueError):
    """Raised when an amount is not a positive number."""


class Account:
    _id_counter = itertools.count(1001)   # class-level, shared by all accounts

    def __init__(self, owner, opening_balance=0):
        if opening_balance < 0:
            raise InvalidAmountError("Opening balance cannot be negative.")
        self.account_no = next(Account._id_counter)
        self.owner = owner
        self.__balance = opening_balance          # private (name-mangled)
        self.transactions = []
        self._log("OPEN", opening_balance)

    # ---------- helpers ----------
    @staticmethod
    def _validate_amount(amount):
        if isinstance(amount, bool) or not isinstance(amount, (int, float)):
            raise InvalidAmountError("Amount must be a number.")
        if amount <= 0:
            raise InvalidAmountError("Amount must be greater than zero.")

    def _log(self, kind, amount):
        self.transactions.append(
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), kind, amount, self.__balance)
        )

    # ---------- core operations ----------
    @property
    def balance(self):
        return self.__balance

    def deposit(self, amount):
        self._validate_amount(amount)
        self.__balance += amount
        self._log("DEPOSIT", amount)
        return self.__balance

    def withdraw(self, amount):
        self._validate_amount(amount)
        if amount > self.__balance:
            raise InsufficientFundsError(
                f"Insufficient funds: balance={self.__balance}, requested={amount}"
            )
        self.__balance -= amount
        self._log("WITHDRAW", amount)
        return self.__balance

    def transfer(self, target, amount):
        if not isinstance(target, Account):
            raise TypeError("Target must be an Account.")
        if target is self:
            raise ValueError("Cannot transfer to the same account.")
        self._validate_amount(amount)
        self.withdraw(amount)          # raises if not enough funds
        target.deposit(amount)
        self.transactions[-1] = (self.transactions[-1][0], f"TRANSFER OUT -> {target.account_no}",
                                 amount, self.balance)
        target.transactions[-1] = (target.transactions[-1][0], f"TRANSFER IN <- {self.account_no}",
                                   amount, target.balance)

    def statement(self):
        print(f"--- Statement for A/C {self.account_no} ({self.owner.name}) ---")
        for t in self.transactions:
            print(t)

    def __str__(self):
        return f"{type(self).__name__}#{self.account_no} | {self.owner.name} | ₹{self.balance}"

    def __repr__(self):
        return f"{type(self).__name__}(owner={self.owner.name!r}, balance={self.balance})"


class SavingsAccount(Account):
    def __init__(self, owner, opening_balance=0, interest_rate=0.04, min_balance=500):
        if opening_balance < min_balance:
            raise InvalidAmountError(f"Opening balance must be at least {min_balance}.")
        super().__init__(owner, opening_balance)
        self.interest_rate = interest_rate
        self.min_balance = min_balance

    def withdraw(self, amount):                      # polymorphism: overriding
        self._validate_amount(amount)
        if self.balance - amount < self.min_balance:
            raise InsufficientFundsError(
                f"Must maintain minimum balance of {self.min_balance}."
            )
        return super().withdraw(amount)

    def add_interest(self):
        interest = round(self.balance * self.interest_rate / 12, 2)
        return self.deposit(interest)


class Customer:
    _cust_counter = itertools.count(1)

    def __init__(self, name):
        if not name or not name.strip():
            raise ValueError("Name is required.")
        self.name = name.strip()
        self.customer_id = next(Customer._cust_counter)
        self.accounts = []

    def open_account(self, kind="current", opening_balance=0, **kwargs):
        if kind == "savings":
            acc = SavingsAccount(self, opening_balance, **kwargs)
        elif kind == "current":
            acc = Account(self, opening_balance)
        else:
            raise ValueError("kind must be 'current' or 'savings'.")
        self.accounts.append(acc)
        return acc

    def get_account(self, account_no):
        for acc in self.accounts:
            if acc.account_no == account_no:
                return acc
        raise KeyError(f"Account {account_no} not found.")

    def total_balance(self):
        return sum(a.balance for a in self.accounts)

    def __str__(self):
        return f"Customer({self.customer_id}, {self.name}, accounts={len(self.accounts)})"


# ---------- demo / quick tests ----------
if __name__ == "__main__":
    ravi = Customer("Ravi")
    anu = Customer("Anu")

    a1 = ravi.open_account("current", 5000)
    a2 = anu.open_account("savings", 10000, interest_rate=0.05, min_balance=1000)

    a1.deposit(1500)
    a1.withdraw(500)
    a1.transfer(a2, 2000)
    a2.add_interest()

    print(a1)
    print(a2)
    print("Ravi total:", ravi.total_balance())

    for bad in (
        lambda: a1.deposit(-10),
        lambda: a1.withdraw(10**6),
        lambda: a2.withdraw(12000),        # breaks min balance
        lambda: a1.transfer(a1, 10),
        lambda: a1.deposit("100"),
    ):
        try:
            bad()
        except Exception as e:
            print(type(e).__name__, "->", e)

    a1.statement()
    a2.statement()

