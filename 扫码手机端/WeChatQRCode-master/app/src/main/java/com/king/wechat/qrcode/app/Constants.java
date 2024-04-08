package com.king.wechat.qrcode.app;

public class Constants {

    public static String MAGIC = "xiaowangniujin";

    public static String MONEY = "$";
    public static String COMPANY = "小王牛筋";
    public static String PRINT = "打单";
    public static String PICK = "配货";
    public static String DELIVERY = "送货";
    public static String COORDINAT = "对接";
    public static String RECEIVE = "对接送货";
    //默认角色
    public static String DEFAULT = "服务";



    public static String ORDER_ID = "订单编号";


    public static final String PREFS_ORDER_NAME = "OrderPrefs";

    public static final String LOGIN_URL = "https://open.feishu.cn/open-apis/bitable/v1/apps/IqF6bLQtla2KrKsDj1JcrN0cn7b/tables/tbl54NTtk5BEnycH/records/search?page_size=20";

    public  enum ErrorCode {
        /**
         * 网络错误
         */
        NETWORK_ERROR(1, "!"),

        /**
         * 飞书调用失败
         */
        FEISHU_ERROR(2, "~"),
        /**
         * 飞书调用成功 但是无记录
         */
        FEISHU_NO_RECORD(3, ".");

        // 枚举属性定义
        private final int code;
        private final String msg;

        // 枚举构造器是私有的
        ErrorCode(int code, String msg) {
            this.code = code;
            this.msg = msg;
        }

        // 对外提供获取枚举属性值的方法
        public int getCode() {
            return code;
        }

        public String getMsg() {
            return msg;
        }
    }


}


