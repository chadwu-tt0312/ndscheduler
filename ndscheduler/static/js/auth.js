/**
 * 認證相關功能
 */

define([], function () {
    'use strict';

    var auth = {};

    /**
     * 從 cookie 中獲取用戶資訊
     */
    auth.getCookie = function (name) {
        var value = "; " + document.cookie;
        var parts = value.split("; " + name + "=");
        if (parts.length == 2) {
            var cookieValue = parts.pop().split(";").shift();
            // 如果 cookie 值包含 '|'，表示是特殊格式的 token
            if (cookieValue.includes("|")) {
                var tokenParts = cookieValue.split("|");
                // token 值在第 5 個部分（索引 4）
                var tokenWithLength = tokenParts[4];
                // 如果 token 包含長度前綴（例如 "288:"），去除它
                if (tokenWithLength.includes(":")) {
                    return tokenWithLength.split(":")[1];
                }
                return tokenWithLength;
            }
            // 如果 cookie 值包含長度前綴（例如 "288:"），去除它
            if (cookieValue.includes(":")) {
                return cookieValue.split(":")[1];
            }
            return cookieValue;
        }
        return null;
    };

    /**
     * 解析 JWT token 中的用戶資訊
     */
    auth.parseJwt = function (token) {
        try {
            if (!token) {
                // console.log("No token found");
                return null;
            }

            // 解碼 base64url 格式的 token
            function base64UrlDecode(str) {
                try {
                    // 將 base64url 轉換為標準 base64
                    str = str.replace(/-/g, "+").replace(/_/g, "/");
                    // 添加填充
                    while (str.length % 4) {
                        str += "=";
                    }
                    // 先嘗試 UTF-8 解碼
                    try {
                        return decodeURIComponent(
                            Array.prototype.map
                                .call(atob(str), function (c) {
                                    return "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2);
                                })
                                .join("")
                        );
                    } catch (e) {
                        // 如果 UTF-8 解碼失敗，直接返回原始解碼結果
                        return atob(str);
                    }
                } catch (e) {
                    console.error("Base64 decode error:", e);
                    return null;
                }
            }

            // 先解碼整個 token
            var decodedToken = base64UrlDecode(token);

            // 檢查解碼後的 token 是否是 JWT 格式
            if (decodedToken.includes("eyJ")) {
                // 使用解碼後的 token 進行 JWT 解析
                var parts = decodedToken.split(".");
                if (parts.length === 3) {
                    try {
                        var payload = JSON.parse(base64UrlDecode(parts[1]));
                        return payload;
                    } catch (e) {
                        console.error("Failed to parse JWT payload:", e);
                    }
                }
            }

            // 如果不是 JWT 格式或解析失敗，嘗試直接解析
            try {
                var payload = JSON.parse(decodedToken);
                // console.log("Parsed payload directly:", payload);
                return payload;
            } catch (e) {
                console.error("Failed to parse token as JSON:", e);
                return null;
            }
        } catch (e) {
            console.error("Token parsing error:", e);
            return null;
        }
    };

    /**
     * 刪除 cookie
     */
    auth.deleteCookie = function (name) {
        document.cookie = name + "=; expires=Thu, 01 Jan 1970 00:00:01 GMT; path=/;";
    };

    /**
     * 登出功能
     */
    auth.logout = function () {
        auth.deleteCookie("token");
        window.location.href = "/login";
    };

    /**
     * 驗證用戶身份並返回用戶信息
     */
    auth.verifyUser = function () {
        // console.log("開始驗證用戶身份");

        // 先檢查 cookie
        var token = auth.getCookie("token");

        // 默認結果
        var result = {
            isAdmin: false,
            username: "",
            isLoggedIn: false
        };

        if (token) {
            // console.log("找到 token，正在解析");
            var user = auth.parseJwt(token);

            if (user) {
                // console.log("成功解析用戶信息:", user.username);
                result.isAdmin = user.is_admin === true;
                result.username = user.username || "";
                result.isLoggedIn = true;

                // 將 body 添加 admin-mode 類，啟用管理員 CSS
                if (result.isAdmin) {
                    document.body.classList.add("admin-mode");
                    // console.log("已啟用管理員模式");
                }
            } else {
                console.warn("Token 解析失敗");
            }
        } else {
            // console.log("未找到 token");

            // 在非登錄頁面時重定向到登錄頁面
            if (window.location.pathname !== "/login") {
                // console.log("非登錄頁面，重定向到登錄頁面");
                window.location.href = "/login";
            }
        }

        return result;
    };

    return auth;
}); 