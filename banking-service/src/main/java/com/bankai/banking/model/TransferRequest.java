package com.bankai.banking.model;

import java.math.BigDecimal;

/** Request body for a transfer between two accounts. */
public class TransferRequest {
    private String toAccountId;
    private BigDecimal amount;
    private String description;

    public String getToAccountId() { return toAccountId; }
    public void setToAccountId(String toAccountId) { this.toAccountId = toAccountId; }
    public BigDecimal getAmount() { return amount; }
    public void setAmount(BigDecimal amount) { this.amount = amount; }
    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }
}
