package com.king.wechat.qrcode.app

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.text.TextUtils
import android.util.Log
import android.view.View
import android.widget.EditText
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.king.wechat.qrcode.app.Constants.ErrorCode


class LoginActivity : AppCompatActivity(){

    // 定义变量来存储EditText控件的引用
    private lateinit var textPhone: EditText
    private lateinit var textPassword: EditText


    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_login)
        // 初始化EditText控件的引用
        textPhone = findViewById(R.id.text_phone)
        textPassword = findViewById(R.id.text_password)
        Log.i(LoginActivity::class.java.simpleName, "onCreate login activity")
    }



    fun onClick(view: View) {
        // 获取输入的手机号码和密码
        val phone = textPhone.text.toString()
        val password = textPassword.text.toString()
        Log.i(LoginActivity::class.java.simpleName, "Phone: $phone, Password: $password")
        // 验证用户名和密码是否为空
        if (TextUtils.isEmpty(phone) || TextUtils.isEmpty(password)) {
            // 一个或两个字段为空，不能进行登录，显示错误消息
            showLoginError(applicationContext, "用户名和密码不能为空")
            return
        }
        //网络请求获取 user 对象
        FeiShuService.queryUser(phone, password, object : UserCallback {
            override fun onSuccess(user: User) {
                runOnUiThread {
                    // 将用户信息写入SharedPreferences
                    val sharedPreferences = application.getSharedPreferences(UserService.PREFS_NAME, Context.MODE_PRIVATE)
                    with(sharedPreferences.edit()) {
                        putString(UserService.PHONE_NUMBER, user.phoneNumber)
                        putString(UserService.USER_ROLE, user.userRole)
                        putString(UserService.USER_NAME, user.userName)
                        apply()
                    }

                    Log.i(LoginActivity::class.java.simpleName, "write user info to sharedPreferences:" +
                            " ${user.userRole} ${user.userName} ${user.phoneNumber}")

                    // 打开 MainActivity
                    val intent = Intent(this@LoginActivity, MainActivity::class.java)

                    intent.putExtra(UserService.USER_NAME, user.userName)
                    intent.putExtra(UserService.USER_ROLE, user.userRole)
                    intent.putExtra(UserService.PHONE_NUMBER, user.phoneNumber)

                    startActivity(intent)
                    finish()
                }
            }

            override fun onError(errorMsg: String, errorCode: ErrorCode) {
                runOnUiThread {
                    showLoginError(this@LoginActivity, "登录失败${errorCode.msg}")
                }
            }
        })


    }

    private fun showLoginError(context: Context, message: String) {
        Toast.makeText(context, message, Toast.LENGTH_LONG).show()
    }

    interface UserCallback {
        fun onSuccess(user: User)
        fun onError(errorMsg: String, errorCode: ErrorCode)
    }
}

