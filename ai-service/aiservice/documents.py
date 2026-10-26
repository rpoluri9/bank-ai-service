"""Seed bank documents for the RAG pipeline.

These are fictional demo-bank documents written for this portfolio project.
They describe the demo bank's fee schedule, account policies, and FAQs, and
they are the only knowledge the AI service answers document questions from.
"""

DOCUMENTS = [
    {
        "id": "fee-schedule",
        "title": "Fee Schedule",
        "text": (
            "Monthly maintenance fee: checking accounts cost 5 dollars per month. "
            "The checking maintenance fee is waived when the account keeps a minimum "
            "daily balance of 500 dollars or more. Savings accounts cost 3 dollars "
            "per month, waived with a minimum daily balance of 300 dollars. "
            "Overdraft fee: this bank does not allow overdrafts. A withdrawal or "
            "transfer that would take an account below zero is declined, and no "
            "overdraft fee is charged. Out-of-network ATM fee: 2 dollars and 50 cents "
            "per withdrawal. Domestic wire transfer fee: 25 dollars. International "
            "wire transfer fee: 45 dollars. Paper statement fee: 2 dollars per month. "
            "Electronic statements are free. Card replacement fee: 5 dollars."
        ),
    },
    {
        "id": "account-policies",
        "title": "Account Policies",
        "text": (
            "Savings accounts earn 2.1 percent annual percentage yield, paid monthly. "
            "Checking accounts earn 0.5 percent annual percentage yield. Interest is "
            "calculated on the daily balance. Transfers between your own accounts are "
            "free and settle instantly. Deposits made before 5 PM are available the "
            "same business day; deposits after 5 PM are available the next business "
            "day. There is no minimum opening deposit for a checking account. A "
            "savings account can be opened with any amount of 25 dollars or more. "
            "Accounts with no activity for 12 months are marked dormant and require "
            "an in-branch visit to reactivate. Joint accounts are supported: both "
            "owners can deposit, withdraw, and transfer."
        ),
    },
    {
        "id": "faqs",
        "title": "Frequently Asked Questions",
        "text": (
            "How do I open an account? Provide your name, choose savings or checking, "
            "and fund it with an opening deposit. How do I check my balance? Use the "
            "banking service balance lookup or ask the AI assistant for your balance. "
            "Can I transfer money to another account? Yes, transfers between accounts "
            "are free and instant, as long as the source account has enough funds. "
            "What happens if I try to withdraw more than my balance? The withdrawal "
            "is declined because overdrafts are not allowed, and your balance does "
            "not change. How do I see my transaction history? Every deposit, "
            "withdrawal, and transfer is recorded in your transaction history with a "
            "timestamp and the balance after the transaction."
        ),
    },
    {
        "id": "loan-basics",
        "title": "Loan Basics",
        "text": (
            "Personal loans start at 7.5 percent annual interest for qualified "
            "applicants, with terms of 12 to 60 months. There is no prepayment "
            "penalty: you can pay a personal loan off early at no extra cost. "
            "A credit check is required for every loan application. Loan decisions "
            "are usually made within 3 business days. Secured loans backed by a "
            "savings balance start at 5.9 percent annual interest."
        ),
    },
]
