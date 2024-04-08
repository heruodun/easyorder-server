package com.king.wechat.qrcode.app;

import static androidx.camera.core.impl.utils.ContextUtil.getApplicationContext;

import static org.opencv.android.NativeCameraView.TAG;

import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageView;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.core.app.ActivityOptionsCompat;
import androidx.fragment.app.Fragment;
import androidx.lifecycle.ViewModelProvider;

import com.king.camera.scan.AnalyzeResult;
import com.king.camera.scan.CameraScan;
import com.king.camera.scan.analyze.Analyzer;
import com.king.wechat.qrcode.WeChatQRCodeDetector;
import com.king.wechat.qrcode.scanning.WeChatCameraScanFragment;
import com.king.wechat.qrcode.scanning.analyze.WeChatScanningAnalyzer;

import org.opencv.OpenCV;

import java.util.List;


/**
 * 扫码tab
 */
public class HomeFragment extends WeChatCameraScanFragment {

    private ImageView ivResult;

    private static int  REQUEST_CODE_QRCODE = 0x10;

    @Override
    public void onCreate(@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        // 初始化OpenCV
        OpenCV.initOpenCV();
        // 初始化WeChatQRCodeDetector
        WeChatQRCodeDetector.init(getActivity());
    }

//如何获取扫码结果


    @Override
    public void initUI() {
        super.initUI();
        ivResult = getRootView().findViewById(R.id.ivResult);
    }

    @Override
    public void onDestroyView() {
        super.onDestroyView();
    }


    private void processQRCodeResult(String scanResultStr, String userName, String userRole) {
        if (scanResultStr != null) {
            Log.d(CameraScan.SCAN_RESULT, scanResultStr);
            int dollarIndex = scanResultStr.indexOf(Constants.MONEY);
            if (dollarIndex == -1) {
                Toast.makeText(getActivity(), "不是" + Constants.COMPANY + "的二维码", Toast.LENGTH_SHORT).show();
                return;
            }
            String beforeDollar = scanResultStr.substring(0, dollarIndex);
            String afterDollar = scanResultStr.substring(dollarIndex + 1);
            if (!Constants.MAGIC.equals(afterDollar)) {
                Toast.makeText(getActivity(), "不是" + Constants.COMPANY + "的二维码", Toast.LENGTH_SHORT).show();
                return;
            }
            long orderId;
            try {
                orderId = Long.parseLong(beforeDollar);
            } catch (NumberFormatException e) {
                Toast.makeText(getActivity(), "不是" + Constants.COMPANY + "的二维码", Toast.LENGTH_SHORT).show();
                return;
            }

            // 获取当前时间戳
            long currentTimestamp = System.currentTimeMillis();

            // 将订单信息写入SharedPreferences，其中orderId作为键，userName和当前时间戳组成的字符串作为值
            SharedPreferences sharedPreferences =
                    getActivity().getApplicationContext().getSharedPreferences(UserService.PREFS_NAME, getActivity().MODE_PRIVATE);
            SharedPreferences.Editor editor = sharedPreferences.edit();
            // 使用逗号作为分隔符
            String value = userName + "," + currentTimestamp;
            editor.putString(Long.toString(orderId), value);
            editor.apply();
            Log.i(
                    Main2Activity.class.toString(),
                    "updateOrderProcess to sharedPreferences success " +
                            orderId + " " + userName + " " + currentTimestamp);
            FeiShuService.updateOrderProcess(
                    orderId,
                    userName,
                    userRole);
            Toast.makeText(getActivity(), scanResultStr, Toast.LENGTH_SHORT).show();
        }
    }


    @Override
    public void onScanResultCallback(@NonNull AnalyzeResult<List<String>> result) {
        // 停止分析
        getCameraScan().setAnalyzeImage(false);
        Log.d(TAG, result.getResult().toString());
        String name = getActivity().getIntent().getStringExtra(UserService.USER_NAME);
        String role = getActivity().getIntent().getStringExtra(UserService.USER_ROLE);
        processQRCodeResult(result.getResult().get(0), name, role);
    }

    @Override
    public void onScanResultFailure() {
        super.onScanResultFailure();
    }

    @Override
    public int getLayoutId() {
        return R.layout.fragment_home;
    }

    @Nullable
    @Override
    public Analyzer<List<String>> createAnalyzer() {
        // 分析器默认不会返回结果二维码的位置信息
//        return WeChatScanningAnalyzer()
        // 如果需要返回结果二维码位置信息，则初始化分析器时，参数传 true 即可
        return new WeChatScanningAnalyzer(true);
    }


}