package com.smartagriculture.config;

import com.zaxxer.hikari.HikariConfig;
import com.zaxxer.hikari.HikariDataSource;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;

import javax.sql.DataSource;

@Configuration
public class DataSourceConfig {

    @Bean
    @Primary
    public DataSource dataSource() {
        AppEnv.JdbcSettings settings = AppEnv.jdbc();
        HikariConfig config = new HikariConfig();
        config.setJdbcUrl(settings.url());
        config.setUsername(settings.username());
        config.setPassword(settings.password());
        config.setMaximumPoolSize(20);
        config.setMinimumIdle(2);
        config.setConnectionTimeout(30_000);
        config.setIdleTimeout(60_000);
        config.setMaxLifetime(3_600_000);
        config.setPoolName("smart-agriculture-pool");
        config.setInitializationFailTimeout(-1);
        return new HikariDataSource(config);
    }
}
