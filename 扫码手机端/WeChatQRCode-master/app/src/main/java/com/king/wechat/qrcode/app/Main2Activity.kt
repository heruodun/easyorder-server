package com.king.wechat.qrcode.app

import android.content.Intent
import android.content.SharedPreferences
import android.os.Bundle
import android.provider.MediaStore
import android.util.Log
import android.view.View
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityOptionsCompat
import androidx.lifecycle.lifecycleScope
import androidx.navigation.NavController
import androidx.navigation.Navigation
import androidx.navigation.ui.AppBarConfiguration
import androidx.navigation.ui.NavigationUI
import com.google.android.material.bottomnavigation.BottomNavigationView
import com.king.camera.scan.CameraScan
import com.king.camera.scan.util.LogUtils
import com.king.opencv.qrcode.OpenCVQRCodeDetector
import com.king.wechat.qrcode.WeChatQRCodeDetector
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.opencv.OpenCV

class Main2Activity : AppCompatActivity() {

    private lateinit var username: String
    private lateinit var userRole: String
    private lateinit var phoneNumber: String

    /**
     * OpenCVQRCodeDetector
     */
    private val openCVQRCodeDetector by lazy {
        OpenCVQRCodeDetector()
    }

    /**
     * 是否使用 WeChatQRCodeDetector 进行检测二维码
     */
    private var useWeChatDetect = false


    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        val navView = findViewById<BottomNavigationView>(R.id.nav_view)
        // Passing each menu ID as a set of Ids because each
        // menu should be considered as top level destinations.
        // Passing each menu ID as a set of Ids because each
        // menu should be considered as top level destinations.
        val appBarConfiguration: AppBarConfiguration = AppBarConfiguration.Builder(
            R.id.navigation_home, R.id.navigation_dashboard)
            .build()
        val navController: NavController =
            Navigation.findNavController(this, R.id.nav_host_fragment_activity_main)
        NavigationUI.setupActionBarWithNavController(this, navController, appBarConfiguration)
        NavigationUI.setupWithNavController(navView, navController)

        // 初始化OpenCV
        OpenCV.initOpenCV()
        // 初始化WeChatQRCodeDetector
        WeChatQRCodeDetector.init(this)
        startActivityForResult(WeChatQRCodeActivity::class.java)

        // 获取传递过来的用户信息
        username = intent.getStringExtra(UserService.USER_NAME).toString()
        userRole = intent.getStringExtra(UserService.USER_ROLE).toString()
        phoneNumber = intent.getStringExtra(UserService.PHONE_NUMBER).toString()

    }

    private fun getContext() = this

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (resultCode == RESULT_OK) {
            when (requestCode) {
                REQUEST_CODE_QRCODE -> processQRCodeResult(data, username, userRole)
                REQUEST_CODE_PICK_PHOTO -> processPickPhotoResult(data)
            }
        }
    }

    /**
     * 处理选择图片后，从图片中检测二维码结果
     */
    @Suppress("DEPRECATION")
    private fun processPickPhotoResult(data: Intent?) {
        data?.let {
            try {
                lifecycleScope.launch {
                    val bitmap = MediaStore.Images.Media.getBitmap(contentResolver, it.data)
                    if (useWeChatDetect) {
                        val result = withContext(Dispatchers.IO) {
                            // 通过WeChatQRCodeDetector识别图片中的二维码
                            WeChatQRCodeDetector.detectAndDecode(bitmap)
                        }
                        if (result.isNotEmpty()) {// 不为空，则表示识别成功
                            // 打印所有结果
                            for ((index, text) in result.withIndex()) {
                                LogUtils.d("result$index:$text")
                            }
                            // 一般需求都是识别一个码，所以这里取第0个就可以；有识别多个码的需求，可以取全部
                            Toast.makeText(getContext(), result[0], Toast.LENGTH_SHORT).show()
                        } else {
                            // 为空表示识别失败
                            LogUtils.d("result = null")
                        }
                    } else {
                        val result = withContext(Dispatchers.IO) {
                            // 通过OpenCVQRCodeDetector识别图片中的二维码
                            openCVQRCodeDetector.detectAndDecode(bitmap)
                        }

                        if (!result.isNullOrEmpty()) {// 不为空，则表示识别成功
                            LogUtils.d("result$result")
                            Toast.makeText(getContext(), result, Toast.LENGTH_SHORT).show()
                        } else {
                            // 为空表示识别失败
                            LogUtils.d("result = null")
                        }
                    }

                }

            } catch (e: Exception) {
                LogUtils.w(e)
            }

        }
    }

    private fun processQRCodeResult(intent: Intent?, userName: String, userRole: String) {
        // 扫码结果
        CameraScan.parseScanResult(intent)?.let { scanResultStr ->
            Log.d(CameraScan.SCAN_RESULT, scanResultStr)
            val dollarIndex = scanResultStr.indexOf(Constants.MONEY);
            if(dollarIndex == -1){
                Toast.makeText(getContext(), "不是"+Constants.COMPANY+"的二维码", Toast.LENGTH_SHORT).show()
                return
            }

            val beforeDollar = scanResultStr.substring(0, dollarIndex)
            val afterDollar = scanResultStr.substring(dollarIndex + 1)
            if(!Constants.MAGIC.equals(afterDollar)) {
                Toast.makeText(getContext(), "不是"+Constants.COMPANY+"的二维码", Toast.LENGTH_SHORT).show()
                return
            }
            val orderId: Long? = beforeDollar.toLongOrNull()
            if(orderId == null) {
                Toast.makeText(getContext(), "不是"+Constants.COMPANY+"的二维码", Toast.LENGTH_SHORT).show()
                return
            }
            // 获取当前时间戳
            val currentTimestamp = System.currentTimeMillis()
            // 将订单信息写入SharedPreferences，其中orderId作为键，currentHandler和当前时间戳组成的字符串作为值
            val sharedPreferences: SharedPreferences =
                applicationContext.getSharedPreferences(UserService.PREFS_NAME, MODE_PRIVATE)
            val editor = sharedPreferences.edit()
            val value = "$userName,$currentTimestamp" // 使用逗号作为分隔符
            editor.putString(orderId.toString(), value)
            editor.apply()
            Log.i(
                Main2Activity::class.java.toString(),
                "updateOrderProcess to sharedPreferences success " +
                        orderId + " " + userName + " " + currentTimestamp)


            FeiShuService.updateOrderProcess(
                orderId,
                userName,
                userRole)

            Toast.makeText(getContext(), scanResultStr, Toast.LENGTH_SHORT).show()
        }

    }

    private fun pickPhotoClicked(useWeChatDetect: Boolean) {
        this.useWeChatDetect = useWeChatDetect
        startPickPhoto()
    }

    private fun startPickPhoto() {
        val pickIntent = Intent(Intent.ACTION_PICK)
        pickIntent.setDataAndType(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, "image/*")
        startActivityForResult(pickIntent, REQUEST_CODE_PICK_PHOTO)
    }

    private fun startActivityForResult(clazz: Class<*>) {
        val options = ActivityOptionsCompat.makeCustomAnimation(this, R.anim.alpha_in, R.anim.alpha_out)
        startActivityForResult(Intent(this, clazz), REQUEST_CODE_QRCODE, options.toBundle())
    }

    fun onClick(view: View) {
        when (view.id) {
//            R.id.btnWeChatQRCodeScan -> startActivityForResult(WeChatQRCodeActivity::class.java)
//            R.id.btnWeChatMultiQRCodeScan -> startActivityForResult(WeChatMultiQRCodeActivity::class.java)
//            R.id.btnWeChatQRCodeDecode -> pickPhotoClicked(true)
//            R.id.btnOpenCVQRCodeScan -> startActivityForResult(OpenCVQRCodeActivity::class.java)
//            R.id.btnOpenCVQRCodeDecode -> pickPhotoClicked(false)
        }
    }

    companion object {
        const val REQUEST_CODE_QRCODE = 0x10
        const val REQUEST_CODE_PICK_PHOTO = 0x11
    }
}
