package com.bankai.banking.exception;

/** Thrown when an account id is not found. Maps to HTTP 404. */
public class AccountNotFoundException extends RuntimeException {
    public AccountNotFoundException(String accountId) {
        super("Account not found: " + accountId);
    }
}
