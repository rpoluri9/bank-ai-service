package com.bankai.banking;

import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.httpBasic;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

/**
 * Proves the security layer: /api/** requires HTTP Basic auth with the
 * local demo user (see application.properties / README "Demo auth").
 */
@SpringBootTest
@AutoConfigureMockMvc
class SecurityTests {

    @Autowired
    private MockMvc mockMvc;

    @Test
    void unauthenticatedRequestIsRejectedWith401() throws Exception {
        mockMvc.perform(get("/api/accounts"))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void wrongPasswordIsRejectedWith401() throws Exception {
        mockMvc.perform(get("/api/accounts")
                        .with(httpBasic("demo", "wrong-password")))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void demoUserCanReachTheApi() throws Exception {
        mockMvc.perform(get("/api/accounts")
                        .with(httpBasic("demo", "demo123")))
                .andExpect(status().isOk());
    }

    @Test
    void demoUserCanCreateAnAccount() throws Exception {
        mockMvc.perform(post("/api/accounts")
                        .with(httpBasic("demo", "demo123"))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"ownerName\":\"Sec\",\"accountType\":\"SAVINGS\",\"openingBalance\":10}"))
                .andExpect(status().isCreated());
    }
}
