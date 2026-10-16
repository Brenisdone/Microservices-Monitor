
package com.brenisdone.log_ingestion.service;

import com.brenisdone.log_ingestion.model.LogEvent;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import tools.jackson.databind.ObjectMapper;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.OffsetDateTime;
import java.time.format.DateTimeParseException;

@Service
public class LogStorageService {

    private final ObjectMapper objectMapper;
    private final Path logFile;

    public LogStorageService(
            ObjectMapper objectMapper,
            @Value("${log-ingestion.storage-file:../log_dashboard/logs.jsonl}")
            String storageFile
    ) {
        this.objectMapper = objectMapper;
        this.logFile = Path.of(storageFile).toAbsolutePath().normalize();
    }

    public synchronized void store(LogEvent event) {
        try {
            OffsetDateTime.parse(event.timestamp());
        } catch (DateTimeParseException ex) {
            throw new IllegalArgumentException(
                    "timestamp must be a valid ISO 8601 timestamp"
            );
        }

        try {
            Files.createDirectories(logFile.getParent());

            String json = objectMapper.writeValueAsString(event);

            Files.writeString(
                    logFile,
                    json + System.lineSeparator(),
                    StandardCharsets.UTF_8,
                    StandardOpenOption.CREATE,
                    StandardOpenOption.APPEND
            );
        } catch (IOException ex) {
            throw new IllegalStateException(
                    "Could not write log event", ex
            );
        }
    }
}
