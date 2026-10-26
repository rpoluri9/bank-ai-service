package com.bankai.banking.events;

import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.Base64;

/**
 * Publishes transaction events to a Google Cloud Pub/Sub topic through the
 * Pub/Sub REST API. This is NOT active by default: it is only wired in when
 * the application is started with {@code pubsub.enabled=true} and the
 * {@code PUBSUB_PROJECT_ID}, {@code PUBSUB_TOPIC}, and
 * {@code PUBSUB_ACCESS_TOKEN} environment variables are set. Without those,
 * the application uses {@link LocalEventPublisher} instead, so everything
 * still runs with no GCP credentials at all.
 */
public class PubSubEventPublisher implements EventPublisher {
    private final String projectId;
    private final String topic;
    private final String accessToken;

    public PubSubEventPublisher(String projectId, String topic, String accessToken) {
        this.projectId = projectId;
        this.topic = topic;
        this.accessToken = accessToken;
    }

    @Override
    public void publish(TransactionEvent event) {
        try {
            String data = Base64.getEncoder().encodeToString(
                    event.toJson().getBytes(StandardCharsets.UTF_8));
            String body = "{\"messages\":[{\"data\":\"" + data + "\"}]}";
            URL url = new URL("https://pubsub.googleapis.com/v1/projects/" + projectId
                    + "/topics/" + topic + ":publish");
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("POST");
            conn.setRequestProperty("Authorization", "Bearer " + accessToken);
            conn.setRequestProperty("Content-Type", "application/json");
            conn.setDoOutput(true);
            try (OutputStream out = conn.getOutputStream()) {
                out.write(body.getBytes(StandardCharsets.UTF_8));
            }
            int status = conn.getResponseCode();
            if (status < 200 || status >= 300) {
                throw new RuntimeException("Pub/Sub publish failed with HTTP " + status);
            }
        } catch (Exception e) {
            throw new RuntimeException("Failed to publish event to Pub/Sub", e);
        }
    }
}
