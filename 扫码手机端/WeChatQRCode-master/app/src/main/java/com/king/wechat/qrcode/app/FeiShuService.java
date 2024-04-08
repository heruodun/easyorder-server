package com.king.wechat.qrcode.app;

import android.util.Log;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;
import java.io.IOException;
import okhttp3.Call;
import okhttp3.Callback;
import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

/**
 * 处理飞书网络请求
 */
public class FeiShuService {
    private static final OkHttpClient client = new OkHttpClient();
    private static String tenantAccessToken; // 将用于存储第一个请求的结果

    private interface TenantTokenCallback {
        void onTokenReceived(String token);
        void onError(IOException e);
    }

    private interface OrderCallback {
        void onOrderReceived(String firstRecordId, JSONArray overallProgress);
        void onError(IOException e);
    }



    public static void queryUser(String username, String password, LoginActivity.UserCallback userCallback) {
        getTenantTokenAsync(new TenantTokenCallback(){

            @Override
            public void onTokenReceived(String token) {
                doQueryUser(username, password, token, userCallback);
            }

            @Override
            public void onError(IOException e) {

            }
        });
    }
    private static void doQueryUser(String username, String password, String token, LoginActivity.UserCallback userCallback) {

        // 调用构造JSON请求体的代码部分
        MediaType jsonMediaType = MediaType.parse("application/json; charset=utf-8");
        RequestBody requestBody = RequestBody.create(buildReqReqBodyJson(username, password), jsonMediaType);

        // 创建请求
        Request request = new Request.Builder()
                .url(Constants.LOGIN_URL)
                .addHeader("Content-Type", "application/json")
                .addHeader("Authorization", "Bearer " + token)
                .post(requestBody)
                .build();

        // 创建OkHttpClient实例
        OkHttpClient client = new OkHttpClient();

        // 发送请求
        client.newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(Call call, IOException e) {
                // 请求失败，处理错误
                userCallback.onError("request network error", Constants.ErrorCode.NETWORK_ERROR);
            }

            @Override
            public void onResponse(Call call, okhttp3.Response response) throws IOException {
                Log.i(FeiShuService.class.toString(), request + " query user " + response);
                if (response.isSuccessful()) {
                    // 解析响应数据
                    String responseData = response.body().string();
                    Log.i(FeiShuService.class.toString(), "response body " + responseData);
                    User user = parseUser(responseData);
                    if(user == null){
                        userCallback.onError("request feishu error", Constants.ErrorCode.FEISHU_ERROR);
                    }
                    else {
                        userCallback.onSuccess(user);
                    }
                    return;
                }

                userCallback.onError("request network error", Constants.ErrorCode.NETWORK_ERROR);
            }
        });

    }


    /**
     * 更新订单进度
     * @param orderId
     * @param userName
     * @return
     */
    public static String updateOrderProcess(Long orderId, String userName, String userRole) {
        new Thread(() -> {
            getTenantTokenAsync(new TenantTokenCallback() {
                @Override
                public void onTokenReceived(String token) {
                    tenantAccessToken = token;
                    // Tenant token received successfully, now execute the second request
                    doGetOrderByOrderId(orderId, tenantAccessToken, new OrderCallback() {

                        @Override
                        public void onOrderReceived(String firstRecordId, JSONArray overallProgress) {
                            Log.i(FeiShuService.class.toString(), "order id:" + orderId + ", id:" + firstRecordId);
                            updateOrderProgressToRemote(tenantAccessToken, firstRecordId, userName, userRole,  overallProgress);
                        }

                        @Override
                        public void onError(IOException e) {

                        }
                    });
                }

                @Override
                public void onError(IOException e) {
                    // Handle errors appropriately
                }

            });
        }).start();
        //todo
        return "";
    }

    private static void getTenantTokenAsync(TenantTokenCallback tenantTokenCallback) {
        MediaType mediaType = MediaType.parse("application/json");
        // 请确保这里的 app_id 和 app_secret 是安全地存储和使用的
        RequestBody body = RequestBody.create(mediaType, "{\"app_id\":\"cli_a57140de9afb5013\",\"app_secret\":\"tFYILUQVlsT7U4jDctg7VdwZWIMZYXbs\"}");
        Request request = new Request.Builder()
                .url("https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal")
                .method("POST", body)
                .addHeader("Content-Type", "application/json")
                .build();

        client.newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(Call call, IOException e) {
                // 异常处理逻辑
                // e.g., 日志记录或用户通知
            }

            @Override
            public void onResponse(Call call, final Response response) throws IOException {
                if (response.isSuccessful()) {
                    try {
                        String responseBody = response.body().string();
                        JSONObject jsonObject = new JSONObject(responseBody);
                        int code = jsonObject.optInt("code");
                        if (code == 0) { // 响应码为0，表示请求成功
                            final String tenantAccessToken = jsonObject.optString("tenant_access_token");
                            tenantTokenCallback.onTokenReceived(tenantAccessToken);
                            // 使用获取到的tenantAccessToken
                            // 通常你需要将下面的逻辑转移到UI线程
                            // e.g., Activity.runOnUiThread(new Runnable() { ... });
                        }
                    } catch (JSONException e) {
                        // JSON解析异常处理
                    } finally {
                        response.close();
                    }
                }
            }
        });
    }


    private static void doGetOrderByOrderId(Long orderId, String tenAntToken, OrderCallback orderCallback) {
        // 请求查询订单表的URL
        String url = "https://open.feishu.cn/open-apis/bitable/v1/apps/SF79bwJc6awjy5sRrQAcSTzNn9L/tables/tblBmGg1sYkSV9GC/records/search?page_size=20";

        // 创建JSON格式的请求体
        MediaType jsonMediaType = MediaType.parse("application/json; charset=utf-8");

        // 在这里，您需要实现buildQueryReqBodyJson方法，该方法应该返回请求体的字符串表示。
        // 假设buildQueryReqBodyJson已经实现并返回正确的JSON格式请求体
        String jsonRequestBody = buildQueryReqBodyJson(orderId);
        RequestBody requestBody = RequestBody.create(jsonRequestBody, jsonMediaType);

        // 创建Request对象
        Request request = new Request.Builder()
                .url(url)
                .addHeader("Content-Type", "application/json")
                .addHeader("Authorization", "Bearer " + tenAntToken)
                .post(requestBody)
                .build();

        // 异步请求
        client.newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(Call call, IOException e) {
                // 请求失败处理
                Log.e("MainActivity", "processQueryOrderFromRemote fail", e);
            }

            @Override
            public void onResponse(Call call, Response response) throws IOException {
                // 此操作在子线程中执行，因此不能直接更新UI
                String responseData = response.body().string();
                Log.i("MainActivity", "processQueryOrderFromRemote " + responseData);

                if (!response.isSuccessful()) {
                    // 处理错误情况
                } else {
                    // 处理成功的响应
                    Log.i("MainActivity", "success " + responseData);

                    try {
                        JSONObject responseJson = new JSONObject(responseData);
                        JSONObject dataObject = responseJson.getJSONObject("data");
                        JSONArray itemsArray = dataObject.getJSONArray("items");

                        // 检查items数组是否有元素
                        if (itemsArray.length() > 0) {
                            JSONObject firstItem = itemsArray.getJSONObject(0);

                            String firstRecordId = firstItem.getString("record_id");
                            JSONArray progresses = firstItem.getJSONObject("fields")
                                    .getJSONArray("总体进度");
                            JSONArray overallprogress = new JSONArray();
                            JSONObject jsonObject = (JSONObject) progresses.get(0);
                            String pStr = (String) jsonObject.get("text");
                            overallprogress = new JSONArray(pStr);
                            orderCallback.onOrderReceived(firstRecordId, overallprogress);

                        } else {
                            // JSON中没有items或items数组为空
                        }
                    } catch (JSONException e) {
                    }



                    // 假设parseJsonResponse方法已经实现并可以解析响应数据
                    // ParsedResult result = parseJsonResponse(responseData);
                    // 根据需要实现updateOrderProgressToRemote等方法和逻辑
                    // 确保在主线程中更新UI
                    // runOnUiThread(() -> {...});

                }
            }
        });
    }

    private static String buildQueryReqBodyJson(long orderId) {
        // 创建最外层的JSONObject
        JSONObject root = new JSONObject();
        try {
            // 创建filter JSONObject
            JSONObject filter = new JSONObject();
            root.put("filter", filter);

            // 设置filter的属性
            filter.put("conjunction", "and");

            // 创建conditions JSONArray
            JSONArray conditions = new JSONArray();
            filter.put("conditions", conditions);

            // 创建一个condition JSONObject并设置它的属性
            JSONObject condition = new JSONObject();
            condition.put("field_name", Constants.ORDER_ID); // 确保Constants.ORDER_ID是您用来标识订单ID字段名的正确常量
            condition.put("operator", "is");
            condition.put("value", new JSONArray().put(orderId));

            // 将condition对象添加到conditions数组
            conditions.put(condition);

        } catch (Exception e) {
            e.printStackTrace();
        }
        // 将root对象转换成字符串并返回
        return root.toString();
    }

    private static String getCurrentProgress(String userRole){
        if(Constants.PICK.equals(userRole) || Constants.PRINT.equals(userRole)
                || Constants.DELIVERY.equals(userRole) || Constants.COORDINAT.equals(userRole)
                || Constants.RECEIVE.equals(userRole)){
            return Constants.PICK;
        }
        return Constants.DEFAULT;
    }

    private static void updateOrderProgressToRemote(String tenantAccessToken, String recordId,
                                                    String userName,String userRole,
                                                    JSONArray overallProgress) {
        // 构建你的Web服务URL，这里是示例URL，你需要根据你的服务来更改
        String url = "https://open.feishu.cn/open-apis/bitable/v1/apps/SF79bwJc6awjy5sRrQAcSTzNn9L/tables/tblBmGg1sYkSV9GC/records/" + recordId;

        // 创建JSON格式的请求体
        MediaType jsonMediaType = MediaType.parse("application/json; charset=utf-8");
        String currentProgress = getCurrentProgress(userRole) ;

        RequestBody requestBody = RequestBody.create(buildUpdateReqBodyJson(currentProgress, userName, overallProgress), jsonMediaType);

        // 创建Request对象
        Request request = new Request.Builder()
                .url(url)
                .addHeader("Content-Type", "application/json")
                .addHeader("Authorization", "Bearer " + tenantAccessToken)
                .put(requestBody)
                .build();

        // 异步请求
        client.newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(Call call, IOException e) {
                // todo 请求失败处理
            }

            @Override
            public void onResponse(Call call, Response response) {
                try {
                    if (!response.isSuccessful()) {
                        Log.e(FeiShuService.class.toString(), request + " update fail " + response);
                        // 处理错误情况
                    } else {
                        // 处理成功的响应
                        final String responseData = response.body().string();
                        JSONObject jsonObject = new JSONObject(responseData);
                        if(jsonObject.getInt("code") == 0){
                            Log.i(FeiShuService.class.toString(), request + "update success " + responseData);
                        }
                        else {
                            Log.e(FeiShuService.class.toString(), request + "update fail " + responseData);

                        }
                        // 注意：以下运行在UI线程的操作是在Android中的一个示例。根据您的环境（如Java桌面应用），这里可能需要不同的线程处理方式。
                        // runOnUiThread(() -> {
                        //    更新UI等操作
                        // });
                    }
                } catch (IOException e) {
                    e.printStackTrace();
                } catch (JSONException e) {
                    throw new RuntimeException(e);
                } finally {
                    response.close();
                }
            }
        });
    }

    /**
     *
     * @param currentProgress 当前进度
     * @param currentHandler 当前处理人
     * @param overallProgress [{"打单人":"xxx","打单时间":"2023-12-29 00:11:00"}]
     * @return
     */
    private static String buildUpdateReqBodyJson(String currentProgress, String currentHandler, JSONArray overallProgress) {
        try {
            // 创建fields的JSONObject
            JSONObject fields = new JSONObject();
            // 向fields对象添加键值对
            fields.put("当前进度", currentProgress);
            fields.put("当前处理人", currentHandler);
            // 解析总体进度JSON数组字符串，并创建JSONArray对象


            // 创建表示当前处理进度的JSONObject
            JSONObject currentProgressDetails = new JSONObject();
            currentProgressDetails.put(currentProgress + "人", currentHandler);
            currentProgressDetails.put(currentProgress+"时间", System.currentTimeMillis());

            // 将当前处理进度详情添加到总体进度的JSONArray中
            overallProgress.put(currentProgressDetails);
            // 将更新后的总体进度JSONArray赋值给fields对象的"总体进度"键
            fields.put("总体进度", overallProgress.toString());
            // 创建最外层的JSONObject并添加fields对象
            JSONObject root = new JSONObject();
            root.put("fields", fields);
            // 将root对象转换为字符串
            Log.i(FeiShuService.class.toString(),  root.toString());
            return root.toString();
        } catch (Exception e) {
            return "{}"; // 返回一个空的JSON对象字符串作为失败的备选
        }
    }



    private static String buildReqReqBodyJson(String phoneNo, String password) {

        JSONObject root = new JSONObject();

        // 创建filter的JSONObject
        JSONObject filter = new JSONObject();

        // 将filter对象添加到根对象
        try {
            root.put("filter", filter);

            // 设置filter的属性
            filter.put("conjunction", "and");

            // 创建conditions的JSONArray
            JSONArray conditions = new JSONArray();

            // 创建第一个条件JSONObject并设置其属性
            JSONObject firstCondition = new JSONObject();
            firstCondition.put("field_name", "手机号码");
            firstCondition.put("operator", "is");
            firstCondition.put("value", new JSONArray().put(phoneNo));

            // 创建第二个条件JSONObject并设置其属性
            JSONObject secondCondition = new JSONObject();
            secondCondition.put("field_name", "密码");
            secondCondition.put("operator", "is");
            secondCondition.put("value", new JSONArray().put(password));


            // 将条件对象添加到条件数组
            conditions.put(firstCondition);
            conditions.put(secondCondition);

            // 将条件数组添加到filter对象
            filter.put("conditions", conditions);
        } catch (JSONException e) {
            throw new RuntimeException(e);
        }

        Log.i(FeiShuService.class.toString(),  "request body " + root);

        return root.toString();

    }

    public static User parseUser(String responseBody) {
        try {
            JSONObject jsonObject = new JSONObject(responseBody);
            JSONObject dataObject = jsonObject.getJSONObject("data");
            int code = jsonObject.getInt("code");
            //正确的返回code
            if(code == 0) {
                JSONArray itemsArray = dataObject.getJSONArray("items");
                for (int i = 0; i < itemsArray.length(); i++) {
                    JSONObject item = itemsArray.getJSONObject(i);
                    JSONObject fields = item.getJSONObject("fields");
                    JSONArray nameArray = fields.getJSONArray("姓名");
                    JSONObject nameObject = nameArray.getJSONObject(0);
                    String username = nameObject.getString("text");
                    String userRole = fields.getString("角色");
                    String userPhone = fields.getString("手机号码");
                    return new User(userPhone, userRole, username);
                }
            }

        } catch (Exception e) {
            // Handle exception
        }
        return null;
    }

}


