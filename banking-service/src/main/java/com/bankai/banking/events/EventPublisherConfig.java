package com.bankai.banking.events;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * Chooses the event publisher. Local publisher by default; the Pub/Sub
 * publisher only when explicitly enabled with real configuration.
 */
@Configuration
public class EventPublisherConfig {

    @Bean
    public EventPublisher eventPublisher(
            @Value("${pubsub.enabled:false}") boolean pubsubEnabled,
            @Value("${PUBSUB_PROJECT_ID:}") String projectId,
            @Value("${PUBSUB_TOPIC:}") String topic,
            @Value("${PUBSUB_ACCESS_TOKEN:}") String accessToken,
            LocalEventPublisher localPublisher) {
        if (pubsubEnabled && !projectId.isBlank() && !topic.isBlank()
                && !accessToken.isBlank()) {
            return new PubSubEventPublisher(projectId, topic, accessToken);
        }
        return localPublisher;
    }
}
