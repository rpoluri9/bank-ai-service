package com.bankai.banking.events;

import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

/** Default publisher: stores events in memory and logs them. Runs offline. */
@Component
public class LocalEventPublisher implements EventPublisher {
    private static final Logger log = LoggerFactory.getLogger(LocalEventPublisher.class);
    private final List<TransactionEvent> events = new CopyOnWriteArrayList<>();

    @Override
    public void publish(TransactionEvent event) {
        events.add(event);
        log.info("EVENT (local publisher): {}", event.toJson());
    }

    public List<TransactionEvent> getEvents() {
        return List.copyOf(events);
    }
}
