
package com.brenisdone.log_ingestion.service;

import com.brenisdone.log_ingestion.model.LogEvent;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import tools.jackson.databind.ObjectMapper;

import java.nio.file.Files;
import java.nio.file.Path;

import static org.junit.jupiter.api.Assertions.*;

class LogStorageServiceTest {

    @TempDir
    Path tempDir;

    @Test
    void writesLogAsJsonLine() throws Exception {
        Path file = tempDir.resolve("logs.jsonl");

        LogStorageService service = new LogStorageService(
                new ObjectMapper(),
                file.toString()
        );

        LogEvent event = new LogEvent(
                "2026-10-16T16:53:12.252Z",
                "payment-service",
                "ERROR",
                "Database connection timeout",
                2500L,
                "storage-test-001"
        );

        service.store(event);

        String content = Files.readString(file);

        assertEquals(1, content.lines().count());
        assertTrue(content.contains("\"correlation_id\":\"storage-test-001\""));
        assertTrue(content.contains("\"duration_ms\":2500"));
    }

    @Test
    void rejectsInvalidTimestamp() {
        Path file = tempDir.resolve("logs.jsonl");

        LogStorageService service = new LogStorageService(
                new ObjectMapper(),
                file.toString()
        );

        LogEvent event = new LogEvent(
                "not-a-timestamp",
                "payment-service",
                "ERROR",
                "Test message",
                100L,
                "storage-test-002"
        );

        assertThrows(
                IllegalArgumentException.class,
                () -> service.store(event)
        );

        assertFalse(Files.exists(file));
    }
}
