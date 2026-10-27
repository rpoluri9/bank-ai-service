package com.bankai.banking.repository;

import java.util.List;
import com.bankai.banking.model.Transaction;
import org.springframework.data.jpa.repository.JpaRepository;

public interface TransactionRepository extends JpaRepository<Transaction, String> {
    /** Full history of one account, in the order the movements happened. */
    List<Transaction> findByAccountIdOrderByTimestampAsc(String accountId);
}
