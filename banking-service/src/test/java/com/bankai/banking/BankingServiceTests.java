package com.bankai.banking;

import static org.hamcrest.Matchers.hasSize;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

@SpringBootTest
@AutoConfigureMockMvc
class BankingServiceTests {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    private String createAccount(String owner, String type, String balance) throws Exception {
        MvcResult result = mockMvc.perform(post("/api/accounts")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"ownerName\":\"" + owner + "\",\"accountType\":\"" + type
                                + "\",\"openingBalance\":" + balance + "}"))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.ownerName").value(owner))
                .andExpect(jsonPath("$.balance").value(Double.parseDouble(balance)))
                .andReturn();
        return objectMapper.readTree(result.getResponse().getContentAsString())
                .get("id").asText();
    }

    @Test
    void createAccountReturnsAccountWithOpeningBalance() throws Exception {
        createAccount("Ramesh Poluri", "SAVINGS", "1000");
    }

    @Test
    void createAccountRejectsBadAccountType() throws Exception {
        mockMvc.perform(post("/api/accounts")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"ownerName\":\"Test\",\"accountType\":\"NOPE\",\"openingBalance\":0}"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.status").value(400))
                .andExpect(jsonPath("$.message").exists());
    }

    @Test
    void createAccountRejectsNegativeOpeningBalance() throws Exception {
        mockMvc.perform(post("/api/accounts")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"ownerName\":\"Test\",\"accountType\":\"SAVINGS\",\"openingBalance\":-5}"))
                .andExpect(status().isBadRequest());
    }

    @Test
    void depositIncreasesBalance() throws Exception {
        String id = createAccount("Asha", "CHECKING", "500");
        mockMvc.perform(post("/api/accounts/" + id + "/deposit")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"amount\":250,\"description\":\"Paycheck\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.balance").value(750.0));
    }

    @Test
    void withdrawDecreasesBalance() throws Exception {
        String id = createAccount("Asha", "CHECKING", "500");
        mockMvc.perform(post("/api/accounts/" + id + "/withdraw")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"amount\":200,\"description\":\"ATM\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.balance").value(300.0));
    }

    @Test
    void withdrawRejectsOverdraft() throws Exception {
        String id = createAccount("Asha", "CHECKING", "100");
        mockMvc.perform(post("/api/accounts/" + id + "/withdraw")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"amount\":101,\"description\":\"Too much\"}"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.message").value(
                        "Insufficient funds: this transaction would overdraw the account"));
        // Balance is unchanged after the failed withdrawal.
        mockMvc.perform(get("/api/accounts/" + id))
                .andExpect(jsonPath("$.balance").value(100.0));
    }

    @Test
    void depositRejectsNonPositiveAmount() throws Exception {
        String id = createAccount("Asha", "CHECKING", "100");
        mockMvc.perform(post("/api/accounts/" + id + "/deposit")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"amount\":0,\"description\":\"Zero\"}"))
                .andExpect(status().isBadRequest());
    }

    @Test
    void transferMovesMoneyBetweenAccounts() throws Exception {
        String from = createAccount("Sender", "CHECKING", "1000");
        String to = createAccount("Receiver", "SAVINGS", "100");
        mockMvc.perform(post("/api/accounts/" + from + "/transfer")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"toAccountId\":\"" + to + "\",\"amount\":400,\"description\":\"Rent\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.balance").value(600.0));
        mockMvc.perform(get("/api/accounts/" + to))
                .andExpect(jsonPath("$.balance").value(500.0));
    }

    @Test
    void transferRejectsOverdraft() throws Exception {
        String from = createAccount("Sender", "CHECKING", "50");
        String to = createAccount("Receiver", "SAVINGS", "0");
        mockMvc.perform(post("/api/accounts/" + from + "/transfer")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"toAccountId\":\"" + to + "\",\"amount\":51,\"description\":\"Too much\"}"))
                .andExpect(status().isBadRequest());
    }

    @Test
    void transferToSameAccountIsRejected() throws Exception {
        String id = createAccount("Solo", "CHECKING", "100");
        mockMvc.perform(post("/api/accounts/" + id + "/transfer")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"toAccountId\":\"" + id + "\",\"amount\":10,\"description\":\"Self\"}"))
                .andExpect(status().isBadRequest());
    }

    @Test
    void transactionHistoryRecordsEveryMovement() throws Exception {
        String id = createAccount("Hist", "SAVINGS", "1000");
        mockMvc.perform(post("/api/accounts/" + id + "/deposit")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"amount\":100,\"description\":\"Extra\"}"))
                .andExpect(status().isOk());
        mockMvc.perform(post("/api/accounts/" + id + "/withdraw")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"amount\":50,\"description\":\"Cash\"}"))
                .andExpect(status().isOk());
        // Opening balance deposit + deposit + withdrawal = 3 entries.
        mockMvc.perform(get("/api/accounts/" + id + "/transactions"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(3)))
                .andExpect(jsonPath("$[2].type").value("WITHDRAWAL"))
                .andExpect(jsonPath("$[2].balanceAfter").value(1050.0));
    }

    @Test
    void unknownAccountReturns404WithCleanErrorBody() throws Exception {
        mockMvc.perform(get("/api/accounts/does-not-exist"))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.status").value(404))
                .andExpect(jsonPath("$.path").value("/api/accounts/does-not-exist"));
    }

    @Test
    void errorBodyAlwaysHasStatusErrorMessageAndPath() throws Exception {
        mockMvc.perform(post("/api/accounts")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"ownerName\":\"\",\"accountType\":\"SAVINGS\",\"openingBalance\":0}"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.status").exists())
                .andExpect(jsonPath("$.error").exists())
                .andExpect(jsonPath("$.message").exists())
                .andExpect(jsonPath("$.path").exists());
    }
}
