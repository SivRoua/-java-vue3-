// API配置
const API_BASE_URL = 'http://localhost:5000/api';

export const API_ENDPOINTS = {
    // 传感器数据
    SENSOR_DATA: `${API_BASE_URL}/sensor-data`,
    
    // 设备控制
    DEVICE_STATUS: `${API_BASE_URL}/device/status`,
    DEVICE_CONTROL: `${API_BASE_URL}/device/control`,
    
    // 用户认证
    LOGIN: `${API_BASE_URL}/auth/login`,
    REGISTER: `${API_BASE_URL}/auth/register`,
    LOGOUT: `${API_BASE_URL}/auth/logout`,
    USER_INFO: `${API_BASE_URL}/auth/profile`,
    
    // 用户管理
    USER_LIST: `${API_BASE_URL}/users`,
    USER_CREATE: `${API_BASE_URL}/users`,
    USER_UPDATE: `${API_BASE_URL}/users`,
    USER_DELETE: `${API_BASE_URL}/users`,
    
    // 警报规则
    ALERT_RULES: `${API_BASE_URL}/alert/rules`,
    ALERT_LOGS: `${API_BASE_URL}/alert/logs`,
    
    // 数据导出
    EXPORT_DATA: `${API_BASE_URL}/export/data`,
    EXPORT_LOGS: `${API_BASE_URL}/export/logs`,
};

// API请求配置
export const API_CONFIG = {
    headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    },
    credentials: 'include', // 支持跨域请求携带cookie
};

// API响应状态码
export const API_STATUS = {
    SUCCESS: 200,
    BAD_REQUEST: 400,
    UNAUTHORIZED: 401,
    FORBIDDEN: 403,
    NOT_FOUND: 404,
    SERVER_ERROR: 500,
};

// API请求超时时间（毫秒）
export const API_TIMEOUT = 10000; 