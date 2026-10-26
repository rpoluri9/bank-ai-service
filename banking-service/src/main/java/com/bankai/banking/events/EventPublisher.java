package com.bankai.banking.events;

/**
 * Publishes transaction events. Two implementations exist:
 * <ul>
 *   <li>{@link LocalEventPublisher} — the default. Keeps events in memory and
 *   logs them. No cloud setup needed; this is what runs out of the box.</li>
 *   <li>{@link PubSubEventPublisher} — used only when
 *   {@code pubsub.enabled=true} plus a project id, topic, and access token are
 *   configured. It calls the Google Cloud Pub/Sub REST API directly, so no
 *   Google client library is required.</li>
 * </ul>
 */
public interface EventPublisher {
    void publish(TransactionEvent event);
}
