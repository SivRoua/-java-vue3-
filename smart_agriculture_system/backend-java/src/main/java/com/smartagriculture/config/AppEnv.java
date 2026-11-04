package com.smartagriculture.config;

import java.io.IOException;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * 环境配置加载器：优先读取系统环境变量，其次读取 .env 文件，最后使用默认值。
 * .env 位于 backend-java/.env（含数据库连接信息，已被 .gitignore 排除）。
 */
public final class AppEnv {

    private static final Map<String, String> FILE_VALUES = new LinkedHashMap<>();

    static {
        loadDotEnv();
    }

    private AppEnv() {
    }

    private static void loadDotEnv() {
        String userDir = System.getProperty("user.dir", ".");
        List<Path> candidates = List.of(
                Paths.get(userDir, ".env"),
                Paths.get(userDir, "backend-java", ".env"),
                Paths.get(userDir, "..", "backend-java", ".env")
        );
        for (Path candidate : candidates) {
            if (!Files.isRegularFile(candidate)) {
                continue;
            }
            try {
                for (String line : Files.readAllLines(candidate, StandardCharsets.UTF_8)) {
                    String trimmed = line.trim();
                    if (trimmed.isEmpty() || trimmed.startsWith("#")) {
                        continue;
                    }
                    int eq = trimmed.indexOf('=');
                    if (eq <= 0) {
                        continue;
                    }
                    String key = trimmed.substring(0, eq).trim();
                    String value = trimmed.substring(eq + 1).trim();
                    if ((value.startsWith("\"") && value.endsWith("\""))
                            || (value.startsWith("'") && value.endsWith("'"))) {
                        value = value.substring(1, value.length() - 1);
                    }
                    FILE_VALUES.putIfAbsent(key, value);
                }
            } catch (IOException ignored) {
                // 读取失败时忽略，继续使用默认值
            }
        }
    }

    public static String get(String key, String defaultValue) {
        String env = System.getenv(key);
        if (env != null && !env.isBlank()) {
            return env;
        }
        String property = System.getProperty(key);
        if (property != null && !property.isBlank()) {
            return property;
        }
        String fileValue = FILE_VALUES.get(key);
        if (fileValue != null && !fileValue.isBlank()) {
            return fileValue;
        }
        return defaultValue;
    }

    public static String jwtSecret() {
        return get("JWT_SECRET_KEY", "your-secret-key-here");
    }

    public static JdbcSettings jdbc() {
        String raw = get("DATABASE_URL", "mysql+pymysql://root:123456@localhost/smart_agriculture?charset=utf8mb4");
        return parseDatabaseUrl(raw);
    }

    /**
     * 将 SQLAlchemy 风格的 DATABASE_URL 转换为 JDBC 连接信息。
     */
    static JdbcSettings parseDatabaseUrl(String raw) {
        String url = raw;
        int schemeIndex = url.indexOf("://");
        String rest = schemeIndex >= 0 ? url.substring(schemeIndex + 3) : url;
        int atIndex = rest.lastIndexOf('@');
        String userInfo = atIndex >= 0 ? rest.substring(0, atIndex) : "";
        String hostAndPath = atIndex >= 0 ? rest.substring(atIndex + 1) : rest;

        String username = "";
        String password = "";
        if (!userInfo.isEmpty()) {
            int colon = userInfo.indexOf(':');
            username = decode(colon >= 0 ? userInfo.substring(0, colon) : userInfo);
            password = colon >= 0 ? decode(userInfo.substring(colon + 1)) : "";
        }

        int slash = hostAndPath.indexOf('/');
        String hostPort = slash >= 0 ? hostAndPath.substring(0, slash) : hostAndPath;
        String dbAndQuery = slash >= 0 ? hostAndPath.substring(slash + 1) : "smart_agriculture";
        int query = dbAndQuery.indexOf('?');
        String database = query >= 0 ? dbAndQuery.substring(0, query) : dbAndQuery;

        String host = hostPort;
        int port = 3306;
        int colon = hostPort.lastIndexOf(':');
        if (colon >= 0) {
            host = hostPort.substring(0, colon);
            try {
                port = Integer.parseInt(hostPort.substring(colon + 1));
            } catch (NumberFormatException ignored) {
                port = 3306;
            }
        }

        String jdbcUrl = String.format(
                "jdbc:mysql://%s:%d/%s?useUnicode=true&characterEncoding=utf8&serverTimezone=Asia/Shanghai"
                        + "&useSSL=false&allowPublicKeyRetrieval=true&zeroDateTimeBehavior=convertToNull"
                        + "&tinyInt1isBit=false",
                host, port, database);
        return new JdbcSettings(jdbcUrl, username, password);
    }

    private static String decode(String value) {
        try {
            return URLDecoder.decode(value, StandardCharsets.UTF_8);
        } catch (Exception e) {
            return value;
        }
    }

    public record JdbcSettings(String url, String username, String password) {
    }
}
