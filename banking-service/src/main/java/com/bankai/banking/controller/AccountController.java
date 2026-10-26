package com.bankai.banking.controller;

import java.util.List;
import com.bankai.banking.model.Account;
import com.bankai.banking.model.CreateAccountRequest;
import com.bankai.banking.model.MoneyRequest;
import com.bankai.banking.model.Transaction;
import com.bankai.banking.model.TransferRequest;
import com.bankai.banking.service.BankingService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/** Spring Boot REST APIs for the banking microservice. */
@RestController
@RequestMapping("/api/accounts")
public class AccountController {
    private final BankingService bankingService;

    public AccountController(BankingService bankingService) {
        this.bankingService = bankingService;
    }

    @PostMapping
    public ResponseEntity<Account> createAccount(@RequestBody CreateAccountRequest request) {
        Account account = bankingService.createAccount(
                request.getOwnerName(), request.getAccountType(), request.getOpeningBalance());
        return ResponseEntity.status(HttpStatus.CREATED).body(account);
    }

    @GetMapping
    public List<Account> listAccounts() {
        return bankingService.listAccounts();
    }

    @GetMapping("/{id}")
    public Account getAccount(@PathVariable("id") String id) {
        return bankingService.getAccount(id);
    }

    @PostMapping("/{id}/deposit")
    public Account deposit(@PathVariable("id") String id, @RequestBody MoneyRequest request) {
        return bankingService.deposit(id, request.getAmount(), request.getDescription());
    }

    @PostMapping("/{id}/withdraw")
    public Account withdraw(@PathVariable("id") String id, @RequestBody MoneyRequest request) {
        return bankingService.withdraw(id, request.getAmount(), request.getDescription());
    }

    @PostMapping("/{id}/transfer")
    public Account transfer(@PathVariable("id") String id, @RequestBody TransferRequest request) {
        return bankingService.transfer(
                id, request.getToAccountId(), request.getAmount(), request.getDescription());
    }

    @GetMapping("/{id}/transactions")
    public List<Transaction> transactions(@PathVariable("id") String id) {
        return bankingService.getTransactions(id);
    }
}
