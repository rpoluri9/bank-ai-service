package com.bankai.banking.events;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.UUID;

/** A transaction event published whenever money moves. */
public class TransactionEvent {
    private final String eventId;
    private final String accountId;
    private final String type;
    private final BigDecimal amount;
    private final BigDecimal balanceAfter;
    private final Instant timestamp;

    public TransactionEvent(String accountId, String type,
                            BigDecimal amount, BigDecimal balanceAfter) {
        this.eventId = UUID.randomUUID().toString();
        this.accountId = accountId;
        this.type = type;
        this.amount = amount;
        this.balanceAfter = balanceAfter;
        this.timestamp = Instant.now();
    }

    public String getEventId() { return eventId; }
    public String getAccountId() { return accountId; }
    public String getType() { return type; }
    public BigDecimal getAmount() { return amount; }
    public BigDecimal getBalanceAfter() { return balanceAfter; }
    public Instant getTimestamp() { return timestamp; }

    /** Minimal JSON rendering without a JSON library dependency. */
    public String toJson() {
        return "{\"eventId\":\"" + eventId + "\",\"accountId\":\"" + accountId
                + "\",\"type\":\"" + type + "\",\"amount\":" + amount
                + ",\"balanceAfter\":" + balanceAfter
                + ",\"timestamp\":\"" + timestamp + "\"}";
    }
}
