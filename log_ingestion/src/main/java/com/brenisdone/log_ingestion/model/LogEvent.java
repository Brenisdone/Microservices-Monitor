
package com.brenisdone.log_ingestion.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.PositiveOrZero;

public record LogEvent(
        @NotBlank
        String timestamp,

        @NotBlank
        String service,

        @NotBlank
        String level,

        @NotBlank
        String message,

        @JsonProperty("duration_ms")
        @NotNull
        @PositiveOrZero
        Long durationMs,

        @JsonProperty("correlation_id")
        @NotBlank
        String correlationId
) {}
