package com.bankai.banking.exception;

/** Thrown when a request fails validation (bad amount, blank name, bad type). */
public class ValidationException extends RuntimeException {
    public ValidationException(String message) {
        super(message);
    }
}
