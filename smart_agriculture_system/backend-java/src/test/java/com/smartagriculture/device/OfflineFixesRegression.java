package com.smartagriculture.device;

import com.smartagriculture.controller.*;
import com.smartagriculture.model.*;
import com.smartagriculture.repository.*;
import com.smartagriculture.security.*;
import com.smartagriculture.service.*;
import java.time.*;
import java.util.*;
import java.lang.reflect.Proxy;
import jakarta.servlet.http.*;
import jakarta.servlet.ServletOutputStream;
import jakarta.servlet.WriteListener;

/** Offline regressions: no sockets or database connections. */
public class OfflineFixesRegression {
    static void check(boolean ok, String message) { if (!ok) throw new AssertionError(message); }
    static class Sensor extends WsnClient {
        boolean online = true; int reads, commands;
        Map<String, Double> values = Map.of("air_temperature",25.0,"air_humidity",50.0);
        Sensor() { super("127.0.0.1", 4000); }
        @Override public synchronized boolean sendCommand(String type, String action) { commands++; return true; }
        @Override public boolean isConnected() { return online; }
        @Override public synchronized Map<String, Double> getSensorData() { reads++; return values; }
    }
    static class Records extends SensorDataRepository {
        LocalDateTime start, end;
        Records() { super(null); }
        @Override public List<SensorData> findBetween(LocalDateTime s, LocalDateTime e) { start=s; end=e; return List.of(); }
    }
    public static void main(String[] args) throws Exception {
        Sensor sensor = new Sensor(); DeviceManager devices = new DeviceManager(sensor);
        var first = devices.getSensorSnapshot(); var cached = devices.getSensorSnapshot();
        check(first.timestamp().equals(cached.timestamp()) && "cache".equals(cached.source()) && sensor.reads==1,"cache relabelled as a new sample");
        sensor.online=false; check(devices.getSensorData().isEmpty(),"offline cache used as a new reading");
        Sensor empty = new Sensor(); empty.values=Map.of();
        check(new DeviceManager(empty).getSensorData().isEmpty(),"empty reading fabricated metrics");
        Records dates=new Records(); new HistoryController(dates).getHistoryData("2026-11-16","2026-11-16",null);
        check(dates.end.isAfter(LocalDateTime.of(2026,11,16,23,59,59)),"end date excludes selected day");
        SensorData sample = SensorData.of(Map.of("air_temperature",25.0,"air_humidity",50.0,"soil_temperature",20.0,
                "soil_moisture",40.0,"light_intensity",10000.0,"co2_concentration",500.0),LocalDateTime.of(2026,11,16,14,0));
        SensorDataRepository exportRecords = new SensorDataRepository(null) {
            @Override public List<SensorData> findBetween(LocalDateTime s,LocalDateTime e) { return List.of(sample); }
            @Override public List<SensorData> findBetweenDesc(LocalDateTime s,LocalDateTime e) { return List.of(sample); }
        };
        var rows = (List<?>)new HistoryController(exportRecords).getHistoryData(null,null,null).getBody();
        var row = (Map<?,?>)rows.get(0);
        String csv = new String(new RootController(devices,exportRecords).exportSensorData(null,null,null).getBody(),java.nio.charset.StandardCharsets.UTF_8);
        String[] cells = csv.split("\r\n")[1].split(",");
        String[] metrics = {"air_temperature","air_humidity","soil_temperature","soil_moisture","light_intensity","co2_concentration"};
        for(int i=0;i<metrics.length;i++) check(Double.parseDouble(cells[i+1])==((Number)row.get(metrics[i])).doubleValue(),"CSV and history differ: "+metrics[i]);
        int[] logCount = {0};
        AutoControlManager automatic=new AutoControlManager(devices, new OperationLogRepository(null) {
            @Override public int insert(OperationLog entry) { logCount[0]++; return 1; }
        });
        check(!automatic.updateThresholds(Map.of("temperature",new double[]{40,10})),"invalid range accepted");
        check(!automatic.updateThresholds(Map.of("temperature",new double[]{0,Double.NaN})),"NaN accepted");
        Map<String,double[]> mixed=new LinkedHashMap<>(); mixed.put("temperature",new double[]{10,20}); mixed.put("humidity",new double[]{90,10});
        check(!automatic.updateThresholds(mixed) && automatic.getThresholds().get("temperature").get("max")==30,"partial update committed");
        check(automatic.updateThresholds(Map.of("temperature",new double[]{10,20})),"valid range rejected");
        var evaluate = AutoControlManager.class.getDeclaredMethod("checkThresholds", Map.class); evaluate.setAccessible(true);
        evaluate.invoke(automatic, Map.of("air_temperature", 25.0));
        check(sensor.commands == 0, "disabled controller sent command");
        var running = AutoControlManager.class.getDeclaredField("running"); running.setAccessible(true); running.setBoolean(automatic, true);
        sensor.online = true;
        evaluate.invoke(automatic, Map.of("air_temperature", 25.0));
        check(sensor.commands == 1 && logCount[0] == 1, "independent controller failed to execute and log");
        evaluate.invoke(automatic, Map.of("air_temperature", 25.0));
        check(sensor.commands == 1, "unchanged state repeated command");
        automatic.stop();
        evaluate.invoke(automatic, Map.of("air_temperature", 5.0));
        check(sensor.commands == 1, "stopped controller sent command");
        check(((Number) automatic.getControlRules().get("temperature").get(1).get("threshold_value")).doubleValue()==20,"display rules differ from active thresholds");
        User user=new User(); user.id=1; user.is_active=false; user.passwordHash=PasswordHasher.hash("changed-password");
        UserRepository users=new UserRepository(null) {
            @Override public User findByUsername(String name) { return user; }
            @Override public User findById(Integer id) { return user; }
        };
        AuthService auth=new AuthService(users);
        check(auth.authenticate("disabled","changed-password")==null,"disabled user authenticated");
        user.is_active=true;
        check(auth.authenticate("admin","admin123")==null,"emergency password still bypasses configured hash");
        JwtUtil jwt=new JwtUtil(); AuthInterceptor interceptor=new AuthInterceptor(jwt,users);
        int[] status={0};
        ServletOutputStream output=new ServletOutputStream() {
            public void write(int b) {} public boolean isReady() { return true; } public void setWriteListener(WriteListener l) {}
        };
        HttpServletResponse response=(HttpServletResponse)Proxy.newProxyInstance(OfflineFixesRegression.class.getClassLoader(),new Class<?>[]{HttpServletResponse.class},(p,m,a)-> {
            if(m.getName().equals("setStatus")) status[0]=(Integer)a[0];
            return m.getName().equals("getOutputStream") ? output : null;
        });
        for(String path:List.of("/api/device/control","/api/auto-control/enable","/api/alerts/handle/1")) {
            check(!interceptor.preHandle(request(path,null),response,null) && status[0]==401,"unauthenticated mutation allowed: "+path);
        }
        String token=jwt.createToken("1",Map.of());
        check(interceptor.preHandle(request("/api/device/control",token),response,null),"active authenticated user rejected");
        user.is_active=false;
        check(!interceptor.preHandle(request("/api/device/control",token),response,null),"disabled user's token still allowed");
        System.out.println("Offline fixes regression checks passed (no network/database access).");
    }
    static HttpServletRequest request(String path,String token) {
        return (HttpServletRequest)Proxy.newProxyInstance(OfflineFixesRegression.class.getClassLoader(),new Class<?>[]{HttpServletRequest.class},(p,m,a)->switch(m.getName()) {
            case "getMethod" -> "POST"; case "getRequestURI" -> path; case "getHeader" -> token==null?null:"Bearer "+token; default -> null;
        });
    }
}
