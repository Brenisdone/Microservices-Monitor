
package com.brenisdone.log_ingestion.controller;

import com.brenisdone.log_ingestion.model.LogEvent;
import com.brenisdone.log_ingestion.service.LogStorageService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/logs")
public class LogController {

    private final LogStorageService storageService;

    public LogController(LogStorageService storageService) {
        this.storageService = storageService;
    }

    @PostMapping
    public ResponseEntity<Map<String, String>> ingestLog(
            @Valid @RequestBody LogEvent event
    ) {
        storageService.store(event);

        return ResponseEntity
                .status(HttpStatus.CREATED)
                .body(Map.of("status", "Log received"));
    }

    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<Map<String, String>> handleInvalidLog(
            IllegalArgumentException ex
    ) {
        return ResponseEntity
                .badRequest()
                .body(Map.of("error", ex.getMessage()));
    }
}
