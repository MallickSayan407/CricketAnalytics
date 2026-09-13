package com.cricketanalytics.ml.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestClient;

@Configuration
public class MLRestClientConfig {

    @Bean
    public RestClient mlRestClient(
            @Value("${ml.api.base-url}") String baseUrl) {

        return RestClient
                .builder()
                .baseUrl(baseUrl)
                .build();
    }
}