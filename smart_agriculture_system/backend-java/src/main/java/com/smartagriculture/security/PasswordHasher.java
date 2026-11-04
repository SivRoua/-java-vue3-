package com.smartagriculture.security;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.SecureRandom;

/**
 * 兼容 werkzeug 的 pbkdf2:sha256 密码哈希格式，保证旧数据库中的账号可直接登录。
 */
public final class PasswordHasher {

    private static final String CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
    private static final SecureRandom RANDOM = new SecureRandom();
    private static final int DEFAULT_ITERATIONS = 260_000;

    private PasswordHasher() {
    }

    public static String hash(String password) {
        String salt = randomSalt(16);
        String digest = pbkdf2Hex(password, salt, DEFAULT_ITERATIONS);
        return "pbkdf2:sha256:" + DEFAULT_ITERATIONS + "$" + salt + "$" + digest;
    }

    /**
     * 校验密码：支持 pbkdf2:sha256 哈希、明文（历史数据）两种格式。
     */
    public static boolean verify(String storedHash, String password) {
        if (storedHash == null || password == null) {
            return false;
        }
        if (!storedHash.startsWith("pbkdf2:")) {
            return storedHash.equals(password);
        }
        String[] parts = storedHash.split("\\$");
        if (parts.length < 3) {
            return false;
        }
        String method = parts[0];
        String salt = parts[1];
        String expected = parts[2];
        if (!method.startsWith("pbkdf2:sha256")) {
            return false;
        }
        int iterations = DEFAULT_ITERATIONS;
        String[] methodParts = method.split(":");
        if (methodParts.length >= 3) {
            try {
                iterations = Integer.parseInt(methodParts[2]);
            } catch (NumberFormatException ignored) {
                iterations = DEFAULT_ITERATIONS;
            }
        } else {
            // 旧版 werkzeug 默认迭代次数
            iterations = 150_000;
        }
        String actual = pbkdf2Hex(password, salt, iterations);
        return MessageDigest.isEqual(
                actual.getBytes(StandardCharsets.UTF_8),
                expected.getBytes(StandardCharsets.UTF_8));
    }

    public static boolean isHashed(String value) {
        return value != null && value.startsWith("pbkdf2:sha256:");
    }

    private static String randomSalt(int length) {
        StringBuilder sb = new StringBuilder(length);
        for (int i = 0; i < length; i++) {
            sb.append(CHARS.charAt(RANDOM.nextInt(CHARS.length())));
        }
        return sb.toString();
    }

    private static String pbkdf2Hex(String password, String salt, int iterations) {
        try {
            javax.crypto.SecretKeyFactory factory =
                    javax.crypto.SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256");
            javax.crypto.spec.PBEKeySpec spec =
                    new javax.crypto.spec.PBEKeySpec(password.toCharArray(), salt.getBytes(StandardCharsets.UTF_8),
                            iterations, 256);
            byte[] bytes = factory.generateSecret(spec).getEncoded();
            StringBuilder sb = new StringBuilder(bytes.length * 2);
            for (byte b : bytes) {
                sb.append(String.format("%02x", b));
            }
            return sb.toString();
        } catch (Exception e) {
            throw new IllegalStateException("密码哈希计算失败", e);
        }
    }
}
