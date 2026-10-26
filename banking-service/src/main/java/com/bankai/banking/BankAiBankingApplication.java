package com.bankai.banking;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/** Bank AI Platform — banking microservice. Runs on port 8080 by default. */
@SpringBootApplication
public class BankAiBankingApplication {
    public static void main(String[] args) {
        SpringApplication.run(BankAiBankingApplication.class, args);
    }
}
