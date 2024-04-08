package com.king.wechat.qrcode.app;

public class User {
    private String phoneNumber;
    private String userRole;
    private String userName;

    public User(String phoneNumber, String userRole, String userName) {
        this.phoneNumber = phoneNumber;
        this.userRole = userRole;
        this.userName = userName;
    }

    @Override
    public String toString() {
        return "User{" +
                "phoneNumber='" + phoneNumber + '\'' +
                ", userRole='" + userRole + '\'' +
                ", userName='" + userName + '\'' +
                '}';
    }

    public String getPhoneNumber() {
        return phoneNumber;
    }

    public void setPhoneNumber(String phoneNumber) {
        this.phoneNumber = phoneNumber;
    }

    public String getUserRole() {
        return userRole;
    }

    public void setUserRole(String userRole) {
        this.userRole = userRole;
    }

    public String getUserName() {
        return userName;
    }

    public void setUserName(String userName) {
        this.userName = userName;
    }
}