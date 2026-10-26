package com.bankai.banking.model;

import java.math.BigDecimal;

/** Request body for creating an account. */
public class CreateAccountRequest {
    private String ownerName;
    private String accountType;
    private BigDecimal openingBalance;

    public String getOwnerName() { return ownerName; }
    public void setOwnerName(String ownerName) { this.ownerName = ownerName; }
    public String getAccountType() { return accountType; }
    public void setAccountType(String accountType) { this.accountType = accountType; }
    public BigDecimal getOpeningBalance() { return openingBalance; }
    public void setOpeningBalance(BigDecimal openingBalance) { this.openingBalance = openingBalance; }
}
