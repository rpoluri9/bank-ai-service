package com.bankai.banking.model;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.UUID;

/** A bank account. Balances are kept as BigDecimal; money is never a double. */
public class Account {
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
