package com.king.wechat.qrcode.app;

import android.content.Context;
import android.content.SharedPreferences;

public class UserService {

    // Key constants for SharedPreferences
    public static final String PREFS_NAME = "user_prefs";
    public static final String PHONE_NUMBER = "user_phone_number";
    public static final String USER_ROLE = "user_role";
    public static final String USER_NAME = "user_name";

    // Method to retrieve user details from SharedPreferences
    public static User getUser(Context context) {
        SharedPreferences sharedPreferences = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        String phoneNumber = sharedPreferences.getString(PHONE_NUMBER, null); // Default to empty string if not found
        String userRole = sharedPreferences.getString(USER_ROLE, null); // Default to empty string if not found
        String userName = sharedPreferences.getString(USER_NAME, null); // Default to empty string if not found
        if(phoneNumber == null || userRole == null || userName == null){
            return null;
        }
        // Assuming User is a class that holds these three properties
        return new User(phoneNumber, userRole, userName);
    }


    public static boolean deleteUser(Context context){
        SharedPreferences sharedPreferences = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        SharedPreferences.Editor editor = sharedPreferences.edit();

        // Clear all data
        editor.clear();

        // Apply changes
        editor.apply();

        // Since we're clearing all data, just return true as there's no simple verification step
        return true;
    }

}

