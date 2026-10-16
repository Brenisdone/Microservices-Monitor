
package com.brenisdone.log_ingestion.controller;

import com.brenisdone.log_ingestion.model.LogEvent;
import com.brenisdone.log_ingestion.service.LogStorageService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(LogController.class)
class LogControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private LogStorageService storageService;

    @Test
    void acceptsValidLogEvent() throws Exception {
        String json = """
                {
                  "timestamp": "2026-10-16T16:53:12.252Z",
                  "service": "payment-service",
                  "level": "ERROR",
                  "message": "Database connection timeout",
                  "duration_ms": 2500,
                  "correlation_id": "automated-test-001"
                }
                """;

        mockMvc.perform(post("/api/logs")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(json))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.status").value("Log received"));

        verify(storageService).store(any(LogEvent.class));
    }

    @Test
    void rejectsLogWithMissingService() throws Exception {
        String json = """
                {
                  "timestamp": "2026-10-16T16:53:12.252Z",
                  "level": "ERROR",
                  "message": "Missing service test",
                  "duration_ms": 100,
                  "correlation_id": "automated-test-002"
                }
                """;

        mockMvc.perform(post("/api/logs")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(json))
                .andExpect(status().isBadRequest());

        verifyNoInteractions(storageService);
    }
}
