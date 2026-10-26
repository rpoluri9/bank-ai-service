package com.bankai.banking.exception;

/** Thrown when a withdrawal or transfer would take the balance below zero. */
public class InsufficientFundsException extends RuntimeException {
    public InsufficientFundsException() {
        super("Insufficient funds: this transaction would overdraw the account");
    }
}
