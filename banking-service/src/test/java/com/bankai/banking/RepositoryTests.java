package com.bankai.banking;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.math.BigDecimal;
import java.util.List;

import com.bankai.banking.model.Account;
import com.bankai.banking.model.Transaction;
import com.bankai.banking.repository.AccountRepository;
import com.bankai.banking.repository.TransactionRepository;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;

/** Repository layer: JPA persistence and the audit-trail ordering rule. */
@DataJpaTest
class RepositoryTests {

    @Autowired
    private AccountRepository accounts;

    @Autowired
    private TransactionRepository transactions;

    @Test
    void accountIsPersistedAndReloaded() {
        Account saved = accounts.save(
                new Account("Repo Owner", "SAVINGS", new BigDecimal("250")));
        assertNotNull(saved.getId());
        Account reloaded = accounts.findById(saved.getId()).orElseThrow();
        assertEquals("Repo Owner", reloaded.getOwnerName());
        assertEquals(0, new BigDecimal("250").compareTo(reloaded.getBalance()));
    }

    @Test
    void transactionHistoryComesBackInInsertionOrder() {
        Account account = accounts.save(
                new Account("Hist Owner", "CHECKING", new BigDecimal("1000")));
        // Explicit distinct timestamps: ordering by timestamp must reproduce
        // the insertion order deterministically.
        java.time.Instant base = java.time.Instant.now();
        Transaction t1 = new Transaction(account.getId(), "DEPOSIT",
                new BigDecimal("100"), new BigDecimal("1100"), "Extra");
        t1.setTimestamp(base);
        Transaction t2 = new Transaction(account.getId(), "WITHDRAWAL",
                new BigDecimal("50"), new BigDecimal("1050"), "Cash");
        t2.setTimestamp(base.plusSeconds(1));
        Transaction t3 = new Transaction(account.getId(), "DEPOSIT",
                new BigDecimal("25"), new BigDecimal("1075"), "Refund");
        t3.setTimestamp(base.plusSeconds(2));
        transactions.save(t1);
        transactions.save(t2);
        transactions.save(t3);

        List<Transaction> history =
                transactions.findByAccountIdOrderByTimestampAsc(account.getId());
        assertEquals(3, history.size());
        assertEquals("DEPOSIT", history.get(0).getType());
        assertEquals("WITHDRAWAL", history.get(1).getType());
        assertEquals("DEPOSIT", history.get(2).getType());
        assertEquals(0, new BigDecimal("1075")
                .compareTo(history.get(2).getBalanceAfter()));
    }

    @Test
    void unknownAccountHasNoHistory() {
        assertTrue(transactions.findByAccountIdOrderByTimestampAsc("no-such-id").isEmpty());
    }
}
