package com.king.wechat.qrcode.app;

import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.util.Log;

import androidx.appcompat.app.AppCompatActivity;

// SplashActivity.java
public class SplashActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        User user = UserService.getUser(this);

        // 根据用户信息是否存在来决定打开哪个 Activity
        Intent intent;
        Log.i(SplashActivity.class.toString(), "sharedPreferences has user " + user);
        if (user != null) {
            // 用户信息存在，打开 MainActivity
            intent = new Intent(this, MainActivity.class);
            intent.putExtra(UserService.USER_NAME, user.getUserName());
            intent.putExtra(UserService.USER_ROLE, user.getUserRole());
            intent.putExtra(UserService.PHONE_NUMBER, user.getPhoneNumber());
        } else {
            // 用户信息不存在，打开 LoginActivity 进行登录
            intent = new Intent(this, LoginActivity.class);
        }

        // 启动相应的 Activity
        startActivity(intent);
        // 关闭当前的 Activity，保证用户回退时不会回到启动界面
        finish();
    }
}

