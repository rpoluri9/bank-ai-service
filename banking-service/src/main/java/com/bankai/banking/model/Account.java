package com.bankai.banking.model;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.UUID;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

/**
 * A bank account, persisted with Spring Data JPA. Balances are kept as
 * BigDecimal; money is never a double. The id is assigned in the constructor
 * (a UUID string), so it is stable across the API, the audit trail, and
 * the AI service's tool calls.
 */
@Entity
@Table(name = "accounts")
public class Account {
    @Id
    private String id;
    private String ownerName;
    private String accountType; // SAVINGS or CHECKING
    private BigDecimal balance;
    private Instant createdAt;

    public Account() {
    }

    public Account(String ownerName, String accountType, BigDecimal openingBalance) {
        this.id = UUID.randomUUID().toString();
        this.ownerName = ownerName;
        this.accountType = accountType;
        this.balance = openingBalance;
        this.createdAt = Instant.now();
    }

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }
    public String getOwnerName() { return ownerName; }
    public void setOwnerName(String ownerName) { this.ownerName = ownerName; }
    public String getAccountType() { return accountType; }
    public void setAccountType(String accountType) { this.accountType = accountType; }
    public BigDecimal getBalance() { return balance; }
    public void setBalance(BigDecimal balance) { this.balance = balance; }
    public Instant getCreatedAt() { return createdAt; }
    public void setCreatedAt(Instant createdAt) { this.createdAt = createdAt; }
}
