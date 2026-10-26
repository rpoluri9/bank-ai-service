package com.bankai.banking.model;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.UUID;

/**
 * One immutable audit-trail entry. Every money movement writes a Transaction,
 * so the full history of an account can always be reconstructed.
 */
public class Transaction {
    private String id;
    private String accountId;
    private String type; // DEPOSIT, WITHDRAWAL, TRANSFER_OUT, TRANSFER_IN
    private BigDecimal amount;
    private BigDecimal balanceAfter;
    private String description;
    private Instant timestamp;

    public Transaction() {
    }

    public Transaction(String accountId, String type, BigDecimal amount,
                       BigDecimal balanceAfter, String description) {
        this.id = UUID.randomUUID().toString();
        this.accountId = accountId;
        this.type = type;
        this.amount = amount;
        this.balanceAfter = balanceAfter;
        this.description = description;
        this.timestamp = Instant.now();
    }

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }
    public String getAccountId() { return accountId; }
    public void setAccountId(String accountId) { this.accountId = accountId; }
    public String getType() { return type; }
    public void setType(String type) { this.type = type; }
    public BigDecimal getAmount() { return amount; }
    public void setAmount(BigDecimal amount) { this.amount = amount; }
    public BigDecimal getBalanceAfter() { return balanceAfter; }
    public void setBalanceAfter(BigDecimal balanceAfter) { this.balanceAfter = balanceAfter; }
    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }
    public Instant getTimestamp() { return timestamp; }
    public void setTimestamp(Instant timestamp) { this.timestamp = timestamp; }
}
