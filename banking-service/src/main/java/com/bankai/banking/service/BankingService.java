package com.bankai.banking.service;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.List;
import java.util.concurrent.atomic.AtomicReference;
import com.bankai.banking.events.EventPublisher;
import com.bankai.banking.events.TransactionEvent;
import com.bankai.banking.exception.AccountNotFoundException;
import com.bankai.banking.exception.InsufficientFundsException;
import com.bankai.banking.exception.ValidationException;
import com.bankai.banking.model.Account;
import com.bankai.banking.model.Transaction;
import com.bankai.banking.repository.AccountRepository;
import com.bankai.banking.repository.TransactionRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * Core banking rules, now persisted with Spring Data JPA (MySQL at runtime,
 * H2 in tests). Every money movement writes an immutable Transaction (the
 * audit trail) and publishes a TransactionEvent. Balances can never go below
 * zero. Transfers lock both accounts in a fixed order to avoid deadlocks.
 */
@Service
@Transactional
public class BankingService {
    private final AccountRepository accounts;
    private final TransactionRepository transactions;
    private final EventPublisher eventPublisher;
    /**
     * Last timestamp handed out. Monotonic: if the clock has not advanced
     * since the previous transaction, the next one gets +1 nanosecond, so
     * history ordered by timestamp is always in insertion order.
     */
    private final AtomicReference<Instant> lastTimestamp =
            new AtomicReference<>(Instant.EPOCH);

    public BankingService(AccountRepository accounts,
                          TransactionRepository transactions,
                          EventPublisher eventPublisher) {
        this.accounts = accounts;
        this.transactions = transactions;
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
        accounts.save(account);
        if (openingBalance.compareTo(BigDecimal.ZERO) > 0) {
            record(account, "DEPOSIT", openingBalance, "Opening balance");
        }
        return account;
    }

    @Transactional(readOnly = true)
    public Account getAccount(String accountId) {
        return accounts.findById(accountId)
                .orElseThrow(() -> new AccountNotFoundException(accountId));
    }

    @Transactional(readOnly = true)
    public List<Account> listAccounts() {
        return accounts.findAll();
    }

    public Account deposit(String accountId, BigDecimal amount, String description) {
        Account account = getAccount(accountId);
        BigDecimal valid = validAmount(amount);
        synchronized (account) {
            account.setBalance(account.getBalance().add(valid));
            accounts.save(account);
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
            accounts.save(account);
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
                accounts.save(from);
                accounts.save(to);
                record(from, "TRANSFER_OUT", valid, description);
                record(to, "TRANSFER_IN", valid, description);
            }
        }
        return from;
    }

    @Transactional(readOnly = true)
    public List<Transaction> getTransactions(String accountId) {
        getAccount(accountId);
        return transactions.findByAccountIdOrderByTimestampAsc(accountId);
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
        tx.setTimestamp(lastTimestamp.updateAndGet(
                prev -> {
                    Instant now = Instant.now();
                    return now.isAfter(prev) ? now : prev.plusNanos(1);
                }));
        transactions.save(tx);
        eventPublisher.publish(new TransactionEvent(
                account.getId(), type, amount, account.getBalance()));
    }
}
