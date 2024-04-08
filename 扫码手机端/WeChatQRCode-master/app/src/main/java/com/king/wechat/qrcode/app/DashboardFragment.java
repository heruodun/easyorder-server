package com.king.wechat.qrcode.app;

import android.content.Intent;
import android.os.Bundle;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.fragment.app.Fragment;


/**
 * 我的tab
 */
public class DashboardFragment extends Fragment {


    public View onCreateView(@NonNull LayoutInflater inflater,
                             ViewGroup container, Bundle savedInstanceState) {
        View view = inflater.inflate(R.layout.fragment_dashboard, container,false);
        TextView nameView = view.findViewById(R.id.text_name);
        TextView phoneView = view.findViewById(R.id.text_phone);
        TextView roleView = view.findViewById(R.id.text_role);

        String name = getActivity().getIntent().getStringExtra(UserService.USER_NAME);
        String role = getActivity().getIntent().getStringExtra(UserService.USER_ROLE) ;
        String phone = getActivity().getIntent().getStringExtra(UserService.PHONE_NUMBER);

        nameView.setText(name);
        phoneView.setText(phone);
        roleView.setText(role);
        return view;
    }

    @Override
    public void onDestroyView() {
        super.onDestroyView();
    }



}