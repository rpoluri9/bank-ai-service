package com.bankai.banking.model;

import java.math.BigDecimal;

/** Request bodies for the money-movement endpoints. */
public class MoneyRequest {
    private BigDecimal amount;
    private String description;

    public BigDecimal getAmount() { return amount; }
    public void setAmount(BigDecimal amount) { this.amount = amount; }
    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }
}
