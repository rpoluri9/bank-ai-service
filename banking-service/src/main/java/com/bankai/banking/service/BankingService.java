package com.bankai.banking.service;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import com.bankai.banking.events.EventPublisher;
import com.bankai.banking.events.TransactionEvent;
import com.bankai.banking.exception.AccountNotFoundException;
import com.bankai.banking.exception.InsufficientFundsException;
import com.bankai.banking.exception.ValidationException;
import com.bankai.banking.model.Account;
import com.bankai.banking.model.Transaction;
import org.springframework.stereotype.Service;

/**
 * Core banking rules. State is held in memory (a portfolio-friendly choice:
 * no database setup is needed to run or test this service). Every money
 * movement writes an immutable Transaction (the audit trail) and publishes a
 * TransactionEvent. Balances can never go below zero.
 */
@Service
public class BankingService {
    private final Map<String, Account> accounts = new ConcurrentHashMap<>();
    private final Map<String, List<Transaction>> history = new ConcurrentHashMap<>();
    private final EventPublisher eventPublisher;

    public BankingService(EventPublisher eventPublisher) {
        this.eventPublisher = eventPublisher;
    }

    public Account createAccount(String ownerName, String accountType, BigDecimal openingBalance) {
        if (ownerName == null || ownerName.isBlank()) {
            throw new ValidationException("ownerName must not be blank");
        }
        if (!"SAVINGS".equalsIgnoreCase(accountType) && !"CHECKING".equalsIgnoreCase(accountType)) {
            throw new ValidationException("accountType must be SAVINGS or CHECKING");
        }
        if (openingBalance == null || openingBalance.compareTo(BigDecimal.ZERO) < 0) {
            throw new ValidationException("openingBalance must be zero or positive");
        }
        Account account = new Account(ownerName, accountType.toUpperCase(), openingBalance);
        accounts.put(account.getId(), account);
        history.put(account.getId(), new ArrayList<>());
        if (openingBalance.compareTo(BigDecimal.ZERO) > 0) {
            record(account, "DEPOSIT", openingBalance, "Opening balance");
        }
        return account;
    }

    public Account getAccount(String accountId) {
        Account account = accounts.get(accountId);
        if (account == null) {
            throw new AccountNotFoundException(accountId);
        }
        return account;
    }

    public List<Account> listAccounts() {
        return new ArrayList<>(accounts.values());
    }

    public Account deposit(String accountId, BigDecimal amount, String description) {
        Account account = getAccount(accountId);
        BigDecimal valid = validAmount(amount);
        synchronized (account) {
            account.setBalance(account.getBalance().add(valid));
            record(account, "DEPOSIT", valid, description);
        }
        return account;
    }

    public Account withdraw(String accountId, BigDecimal amount, String description) {
        Account account = getAccount(accountId);
        BigDecimal valid = validAmount(amount);
        synchronized (account) {
            if (account.getBalance().compareTo(valid) < 0) {
                throw new InsufficientFundsException();
            }
            account.setBalance(account.getBalance().subtract(valid));
            record(account, "WITHDRAWAL", valid, description);
        }
        return account;
    }

    /** Moves money between two accounts. No overdraft on the source account. */
    public Account transfer(String fromAccountId, String toAccountId, BigDecimal amount, String description) {
        if (fromAccountId.equals(toAccountId)) {
            throw new ValidationException("fromAccountId and toAccountId must differ");
        }
        Account from = getAccount(fromAccountId);
        Account to = getAccount(toAccountId);
        BigDecimal valid = validAmount(amount);
        // Lock in a fixed order to avoid deadlocks.
        Account first = from.getId().compareTo(to.getId()) < 0 ? from : to;
        Account second = first == from ? to : from;
        synchronized (first) {
            synchronized (second) {
                if (from.getBalance().compareTo(valid) < 0) {
                    throw new InsufficientFundsException();
                }
                from.setBalance(from.getBalance().subtract(valid));
                to.setBalance(to.getBalance().add(valid));
                record(from, "TRANSFER_OUT", valid, description);
                record(to, "TRANSFER_IN", valid, description);
            }
        }
        return from;
    }

    public List<Transaction> getTransactions(String accountId) {
        getAccount(accountId);
        return List.copyOf(history.getOrDefault(accountId, List.of()));
    }

    private BigDecimal validAmount(BigDecimal amount) {
        if (amount == null || amount.compareTo(BigDecimal.ZERO) <= 0) {
            throw new ValidationException("amount must be greater than zero");
        }
        return amount;
    }

    private void record(Account account, String type, BigDecimal amount, String description) {
        Transaction tx = new Transaction(account.getId(), type, amount,
                account.getBalance(), description == null ? type : description);
        history.get(account.getId()).add(tx);
        eventPublisher.publish(new TransactionEvent(
                account.getId(), type, amount, account.getBalance()));
    }
}
