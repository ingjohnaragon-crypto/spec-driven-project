package com.fabric.open_spec.presentation.controller;

import com.fabric.open_spec.application.dto.HealthResponse;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

class HealthControllerTest {

    @Test
    void shouldReturn200AndHealthPayload() {
        HealthController controller = new HealthController();

        ResponseEntity<HealthResponse> response = controller.getHealth();

        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
        assertEquals("UP", response.getBody().status());
        assertEquals("open-spec", response.getBody().service());
    }
}
